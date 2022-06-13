import errno
import os
from libta import *


class TemplateHelper:
    def __init__(self, template):
        self.template = template
        self.isTA = template.isTA
        self.initial_location = template.init

        self.instances = stdlist_to_list(template.instances)
        self.states = stdlist_to_list(template.states)
        self.branchpoints = stdlist_to_list(template.branchpoints)
        self.edges = stdlist_to_list(template.edges)
        self.variables = stdlist_to_list(template.variables)
        self.functions = stdlist_to_list(template.functions)

    # TODO: addLocation etc. functions that original class has

    def getTemplateObject(self):
        return self.template


class NTAHelper:
    def __init__(self, path, name="nta"):
        self.name = name
        self.ta_system = UTAP.TimedAutomataSystem()

        t = parseXMLFile(path, self.ta_system, True)
        if t != 0:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)

        # Global declarations
        self.declarations = self.ta_system.getGlobals()

        self.templates = []
        for template in self.ta_system.getTemplates():
            self.templates.append(TemplateHelper(template))

        # Queries, since the object is a vector no need to convert it to list 
        self.queries = self.ta_system.getQueries()

    def writeToXML(self, path=""):
        if path != "": # If no path is specified then write with its name to the current path
            t = writeXMLFile(path, self.ta_system)
        else:
            t = writeXMLFile(self.name + ".xml", self.ta_system)

        if t != 0: # t == 0 means no error, so if there is an error, raise an exception
            raise Exception("Could not write to file.")

    def getSystemObject(self): # Returns the original object that is casted from cpp
        return self.ta_system
