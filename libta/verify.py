import subprocess
import re
import os

#TODO: Test
def verify(modelfilename, queryfilename, verifyta='verifyta',
            searchorder='bfs', statespacereduction='1', approximation='', getoutput=False,
            remotehost=None, remotedir='/tmp/'):
    searchorder = { 'bfs': '0', #Breadth first
                    'dfs': '1', #Depth first
                    'rdfs': '2', #Random depth first
                    'ofs': '3', #Optimal first
                    'rodfs': '4', #Random optimal depth first
                    'tfs': '6', #Target first
                    }[searchorder]

    cmdline = ''
    #If we're using a remote host, copy stuff first
    if remotehost:
        scpstuff = 'scp -q ' + modelfilename + ' ' + queryfilename + ' ' + remotehost + ':' + remotedir
        subprocess.check_call(scpstuff, shell=True)

        modelfilename = os.path.join(remotedir, os.path.basename(modelfilename))
        queryfilename = os.path.join(remotedir, os.path.basename(queryfilename))

        cmdline = 'ssh ' + remotehost + ' '
    if approximation == 'over':
        approximation = ' -A '

    cmdline += verifyta + ' -o' + searchorder + ' -S' + statespacereduction + \
        approximation + \
        ' -q ' + modelfilename + ' ' + queryfilename

    #print 'Executing', cmdline
    proc = subprocess.Popen(
        cmdline, 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    #TODO - report progress
    (stdoutdata, stderrdata) = proc.communicate()

    lines = stdoutdata.split('\n')
    errlines = stderrdata.split('\n')

    #Look for tell-tale signs that something went wrong
    for line in errlines:
        if "Internet connection is required for activation." in line:
            raise Exception("UPPAAL verifyta error: " + line)

    regex = re.compile('^Verifying property ([0-9]+) at line ')
    res = []
    lastprop = None
    sub = None
    for line in lines:
        match = regex.match(line)
        if lastprop:
            if line.endswith(' -- Property is satisfied.'):
                res += [True]
            elif line.endswith(' -- Property is NOT satisfied.'):
                res += [False]
            elif line.endswith(' -- Property MAY be satisfied.'):
                res += ['maybe']
            else:
                pass #Ignore garbage
            lastprop = None
        elif line.endswith('sup:'):
            sub = 1
        elif sub:
            res[-1] = line
            sub = None
        elif match:
            lastprop = int(match.group(1))

    if getoutput:
        return (res, stdoutdata)

    return res
