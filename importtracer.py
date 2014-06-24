import builtins
import sys
import time

orig_import = builtins.__import__

def is_pkg(modname):
    try:
        loader = sys.modules[modname].__loader__
    except KeyError:
        return False
    return loader.is_package(modname)



class ImportTracker(object):
    def __init__(self, excludes=None):
        self.importstack = []
        self.record = []
        self.timings = {}
        self.excludes = excludes or []
        self.in_exclude = False

    def _tracking_import(self, name, globals=None, locals=None, fromlist=(), level=0):
        imported_by = self.importstack[-1] if self.importstack else None  

        index = len(self.record)
        self.importstack.append(index)
        self.record.append((name, imported_by, level))
        try:
            tic = time.perf_counter()
            ret = orig_import(name, globals, locals, fromlist, level)
            self.timings[index] = time.perf_counter() - tic
        finally:
            self.importstack.pop()
        return ret
    
    def _process(self):
        self.import_links = il = []
        for i, (name, imported_by, level) in enumerate(self.record):
            if imported_by is None:
                imported_by = ''
            else:
                assert isinstance(imported_by, int)
                imported_by = il[imported_by][0]
            
            if level > 0:
                if is_pkg(imported_by):
                    level -= 1
                if level == 0:
                    full_name = imported_by + '.' + name
                else:
                    full_name = '.'.join(imported_by.split('.')[:-level] + [name])
            else:
                full_name = name
            
            il.append((full_name, imported_by, self.timings.get(i, None)))

    @property
    def filtered_links(self):
        return [l for l in self.import_links if 
                    not any(l[0].startswith(x) for x in self.excludes)]
    
    def dump_nx_graph(self):
        import networkx
        g = networkx.DiGraph()
        for name, imported_by, timing in self.filtered_links:
            # add_edge adds both ends, so filter by imported_by as well
            if not any(imported_by.startswith(x) for x in self.excludes):
                g.add_edge(imported_by, name)
        return g

    def dump_csv(self, fileobj_or_path):
        if isinstance(fileobj_or_path, str):
            with open(fileobj_or_path, 'w') as f:
                return self.dump_csv(f)
        
        import csv
        w = csv.writer(fileobj_or_path)
        w.writerow(['Module', 'Imported by', 'Time'])
        w.writerows(self.filtered_links)

class track(object):
    def __init__(self, **kwargs):
        self.it = ImportTracker(**kwargs)

    def __enter__(self):
        builtins.__import__ = self.it._tracking_import
        return self.it

    def __exit__(self, etype, evalue, tb):
        builtins.__import__ = orig_import
        self.it._process()

def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', help="Dump the import tracking to a CSV file")
    ap.add_argument('--networkx', action='store_true',
                    help="Draw a NetworkX graph of the imports")
    ap.add_argument('-x', '--exclude', action='append',
                    help="Ignore imports in a module or package")
    ap.add_argument('module', help="Import this module to start things off")
    
    options = ap.parse_args(argv)
    
    with track(excludes = options.exclude) as it:
        __import__(options.module)
    
    if options.csv:
        it.dump_csv(options.csv)
    if options.networkx:
        g = it.dump_nx_graph()
        import matplotlib.pyplot as plt
        import networkx
        networkx.draw(g)
        plt.show()

if __name__ == '__main__':
    main()