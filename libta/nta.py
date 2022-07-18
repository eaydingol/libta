import errno
import os
from libta import *


class TemplateHelper:
    def __init__(self, template):
        self.template = template
        self.isTA = template.isTA
        self.initial_location = [
            s for s in template.states if s.uid.getName() == template.init.getName()][0]

        # selist := {location: [edges that goes out from location]}
        # TODO: Change name
        self.selist = {s: []
                       for s in template.states}
        for edge in template.edges:
            self.selist[edge.src].append(edge)

        self.instances = stdlist_to_list(template.instances)
        self.states = stdlist_to_list(template.states)
        self.branchpoints = stdlist_to_list(template.branchpoints)
        self.edges = stdlist_to_list(template.edges)
        self.variables = stdlist_to_list(template.variables)
        self.functions = stdlist_to_list(template.functions)

    def getTemplateObject(self):
        return self.template


class NTAHelper:
    def __init__(self, path="", name="nta"):
        self.name = name
        self.ta_system = UTAP.TimedAutomataSystem()
        self.declarations = []
        self.templates = []
        self.queries = []
        self.__sysbuilder = UTAP.SystemBuilder(self.ta_system)

        if path == "":
            return

        t = parseXMLFile(path, self.ta_system, True)
        if t != 0:
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), path)

        # Global declarations
        self.declarations = self.ta_system.getGlobals()

        # Create TemplateHelper for each template
        for template in self.ta_system.getTemplates():
            self.templates.append(TemplateHelper(template))

        # Queries, since the object is a vector no need to convert it to list
        self.queries = self.ta_system.getQueries()

    def writeToXML(self, path=""):
        if path != "":  # If no path is specified then write with its name to the current path
            t = writeXMLFile(path, self.ta_system)
        else:
            t = writeXMLFile(self.name + ".xml", self.ta_system)

        if t != 0:  # t == 0 means no error, so if there is an error, raise an exception
            raise Exception("Could not write to file.")

    def getSystemObject(self):  # Returns the original object that is casted from cpp
        return self.ta_system

    # Creates an expression that is to be written to the NTA
    # To be used with other template creation functions, as it uses UTAP::SystemBuilder class
    def __createExpression(self, clock, op, rval):
        self.__sysbuilder.exprId(str(clock))
        self.__sysbuilder.exprNat(rval)
        self.__sysbuilder.exprBinary(op)

    # Adds a state to the template, for now just used with an empty template
    def __addState(self, name, invariant=[], is_init=False):  # TODO: Get template and change it
        if invariant is not None:
            f = 0
            for clock, op, rval in invariant:
                self.__createExpression(clock, op, rval)
                if f and len(invariant) > 1:
                    self.__sysbuilder.exprBinary(UTAP.Constants.AND)
                f = 1

        self.__sysbuilder.procState(name, (invariant != []), 0)
        if is_init:
            self.__sysbuilder.procStateInit(name)

    # Adds an edge to the template, for now just used with an empty template
    def __addEdge(self, src, dst, actname, guard=[], update=[], sync=[]):
        self.__sysbuilder.procEdgeBegin(str(src), str(dst), 0, actname)
        if guard != []:
            f = 0
            for clock, op, rval in guard:
                self.__createExpression(clock, op, rval)

                if f and len(guard) > 0:
                    self.__sysbuilder.exprBinary(UTAP.Constants.AND)
                f = 1

            self.__sysbuilder.procGuard()

        if update != []:
            f = 0
            for clock, op, val in update:  # op is always ASSIGN
                self.__createExpression(clock, op, val)

                if f and len(update) > 0:
                    self.__sysbuilder.exprBinary(UTAP.Constants.COMMA)
                f = 1

            self.__sysbuilder.procUpdate()

        if sync != []:
            pass  # TODO
        self.__sysbuilder.procEdgeEnd()

    # Adds clocks to the NTA, must bu called before template creation as clocks should be defined globally
    def addClocks(self, clocks):
        for clock in clocks:
            self.__sysbuilder.typeClock(self.__sysbuilder.PREFIX_NONE)
            self.__sysbuilder.declVar(str(clock), 0)

        self.declarations = self.ta_system.getGlobals()

    # Creates a new template
    # Takes arguments:
    # procname := process name
    # states := list of locations [(location name, [(clock, op, rval)])]
    # edges := list of edges [(source loc, destination loc, action, [(clock, op, rval)], [(clock, ASSIGN, rval)], [])]
    def createTemplate(self, procname, states=[], edges=[]):
        self.__sysbuilder.procBegin(str(procname), True)
        self.__sysbuilder.process(str(procname))

        for s, inv, init in states:
            self.__addState(str(s), inv, init)

        for src, dst, actname, guard, update, sync in edges:
            self.__addEdge(str(src), str(dst), actname,
                           guard, update, sync)  # TODO: Sync

        self.__sysbuilder.procEnd()

        self.templates.append(TemplateHelper(
            self.ta_system.getTemplates().back()))  # Assuming it appends to the end of std::list
