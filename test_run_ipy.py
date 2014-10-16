import importtracer

with importtracer.track(excludes=['numpy']) as it:
    import IPython
    IPython.start_ipython()

# Save these as CSV:
it.dump_csv('ipy_run.csv')
