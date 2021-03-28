# SPDX-License-Identifier: CC0-1.0

from matplotlib._pylab_helpers import Gcf
from matplotlib.backend_bases import (
    _Backend, FigureCanvasBase, FigureManagerBase)
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib import interactive

from io import BytesIO
from subprocess import run

import sys


# XXX heuristic for interactive repl
if sys.flags.interactive:
    interactive(True)


class FigureManagerICat(FigureManagerBase):
    
    @classmethod
    def _run(self, *cmd):
        def f(*args, output=True, **kwargs):
            if output:
                kwargs['capture_output'] = True
                kwargs['text'] = True
            r = run(cmd + args, **kwargs)
            if output:
                return r.stdout.rstrip()
        return f
    
    def show(self):
        icat = __class__._run('kitty', '+kitten', 'icat')
        
        # gather terminal dimensions
        px = icat('--print-window-size')
        px = list(map(int, px.split('x')))

        # resize figure to terminal size & aspect ratio
        dpi = self.canvas.figure.dpi
        size = min(px[0], px[1]) / dpi
        self.canvas.figure.set_size_inches((size, size))
                
        with BytesIO() as buf:
            self.canvas.figure.savefig(buf, format='png', facecolor='#888888')
            icat('--align', 'left', output=False, input=buf.getbuffer())

@_Backend.export
class _BackendICatAgg(_Backend):
    FigureCanvas = FigureCanvasAgg
    FigureManager = FigureManagerICat
    
    # XXX: `trigger_manager_draw` is intended
    # for updates, not one-shot rendering.
    # Thus, we need to filter calls for figures
    # that aren't fully initialized yet, like the
    # call from `plt.figure`. Our heuristic for
    # an initialized figure is the presence of axes.
    def _trigger_manager_draw(manager):
        if manager.canvas.figure.get_axes():
            manager.show()
            Gcf.destroy(manager)
    
    def show(*args, **kwargs):
        _Backend.show(*args, **kwargs)
        Gcf.destroy_all()
    
    trigger_manager_draw = _trigger_manager_draw
    mainloop = lambda: None