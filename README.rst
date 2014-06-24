Trace Python imports

Command line usage::

    python3 importtracer.py [--csv file.csv] [--networkx] [-x pkg [-x ...]] module

This will import ``module``, tracking everything that gets imported. Passing
``--csv`` will dump the results as a CSV file. ``--networkx`` will draw the
graph of imports using `NetworkX <https://networkx.github.io/>`_. ``-x`` options
will exclude packages from the reporting by prefix (the data is still collected,
but not displayed.

Python usage::

    import importtracer
    
    with importtracer.trace(excludes=['numpy']) as it:
        import matplotlib
    
    # The imports made, as (modulename, importedby, time), filtering exclusions
    it.filtered_links

    # Save these as CSV:
    it.dump_csv('file.csv')

    # Make a NetworkX graph
    g = it.dump_nx_graph()
    # Draw the graph
    networkx.draw(g); plt.show()
