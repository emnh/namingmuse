
import urwid
import urwid.raw_display
import sys
import policy
import albumtag

class ListItem(urwid.Button):
    def set_label(self, label):
        self.label = label
        self.w = urwid.Text(label)
        self._invalidate()

class MovePile(urwid.Pile):

    def __init__(self, *args, **kwargs):
        self.isMoving = False
        super(MovePile, self).__init__(*args, **kwargs)
        self.body = self.widget_list

    def set_focus(self, item):
        if self.isMoving:
            body = self.body
            tmp = self.get_focus()
            oldidx = body.index(tmp)
            if isinstance(item, int):
                newidx = item
            else:
                newidx = body.index(item)
            #debug('setfocus %s, %s\n' % (str(oldidx), str(newidx)))
            if newidx != oldidx:
                body[oldidx] = body[newidx]
                body[newidx] = tmp
            super(MovePile, self).set_focus(newidx)
        else:
            super(MovePile, self).set_focus(item)

    def oldkeypress(self, size, key):
        passKey = False
        if self.isMoving:
            body = self.widget_list
            if key == 'up':
                tmp = self.get_focus()
                tmpfocus = body.index(tmp)
                newidx = (tmpfocus - 1) % len(body)
                body[tmpfocus] = body[newidx]
                body[newidx] = tmp
                #debug('up %d, %d\n' % (tmpfocus, newidx))
            elif key == 'down':
                #debug('down\n')
                tmp = self.get_focus()
                tmpfocus = body.index(tmp)
                newidx = (tmpfocus + 1) % len(body)
                body[tmpfocus] = body[newidx]
                body[newidx] = tmp
            else:
                passKey = True
        else:
            passKey = True
        if passKey:
            super(MovePile, self).set_focus(item)
        
def border(w):
    return urwid.AttrWrap(urwid.LineBox(w), 'border')

class OrderTracks(object):
    palette = [
        ('border',         'light gray',      'black', 'standout'),
        ('filename normal',         'light gray',      'black', 'standout'),
        ('body',         'black',      'black'),
        ('header',       'white',      'dark blue',   'bold'),
        ('button normal','light gray', 'dark blue', 'standout'),
        ('button select','white',      'dark green'),
        ('button disabled','dark gray','dark blue'),
        ('edit',         'light gray', 'dark blue'),
        ('chars',        'light gray', 'black'),
        ('exit',         'white',      'dark cyan'),
        ]

    def __init__(self, filelist, album, encoding):
        self.filelist = filelist
        self.album = album
        self.encoding = encoding

    def switchSelect(self, button=None):
        if button == None:
            self.fnameSelected = False
        else:
            self.fnameSelected = not self.fnameSelected
        if self.fnameSelected:
            self.ui.register_palette_entry('filename select',         'black',      'dark red')
        else:
            self.ui.register_palette_entry('filename select',         'black',      'light gray')
        if button != None:
            # force refresh
            self.ui.clear()
            self.newNamesList.isMoving = self.fnameSelected
        
    def setup_view(self):

        # File list
        fnamews = []
        newnamews = []
        tracks = albumtag.namebinder_trackorder(self.filelist, self.album, self.encoding)
        for i, (fpath, track) in enumerate(zip(self.filelist, tracks)):
            fname = fpath.getName()
            fbox = urwid.Text(fname)
            fbox = urwid.AttrWrap(fbox, 'filename normal', 'filename select')
            fnamews.append(fbox)
            newname = policy.genfilename(fpath, self.album, track)
            fbox = ListItem(newname, on_press=self.switchSelect)
            fbox.idx = i
            fbox = urwid.AttrWrap(fbox, 'filename normal', 'filename select')
            newnamews.append(fbox)

        # Left ListBox
        fnames = urwid.Pile(fnamews, focus_item=0)
        fnamesSlw = urwid.SimpleListWalker([fnames])
        lstfnames = border(urwid.ListBox(fnamesSlw))

        # XXX: synchronized scrolling, or better yet, one listbox

        # Right ListBox
        newnames = MovePile(newnamews, focus_item=0)
        self.newNamesList = newnames
        newnamesSlw = urwid.SimpleListWalker([newnames])
        mvl = urwid.ListBox(newnamesSlw)
        lstnewnames = border(mvl)

        col = urwid.Columns([lstfnames, lstnewnames], 1, focus_column=1)
        
        # Frame
        w = urwid.AttrWrap(col, 'body')
        hdr = urwid.Text("Line up the files with their new names")
        hdr = urwid.AttrWrap(hdr, 'header')
        w = urwid.Frame(header=hdr, body=w)

        # Exit message
        exit = urwid.BigText(('exit'," Quit? "), urwid.Thin6x6Font())
        exit = urwid.Overlay(exit, w, 'center', None, 'middle', None)
        return w, exit


    def main(self):
        self.ui = urwid.raw_display.Screen()
        self.ui.register_palette(self.palette)
        self.switchSelect()
        self.ui.set_input_timeouts(5)
        self.view, self.exit_view = self.setup_view()
        self.ui.run_wrapper(self.run)
        self.tracks = []
        for fbox in self.newNamesList.body:
            i = fbox.idx
            self.tracks.append(self.album.tracks[i])
    
    def run(self):
        self.ui.set_mouse_tracking()
        size = self.ui.get_cols_rows()
        show_exit = False
        do_exit = False
        while True:
            if show_exit:
                canvas = self.exit_view.render(size)
            else:
                canvas = self.view.render(size, focus=True)
                
            self.ui.draw_screen(size, canvas)
            if do_exit:
                break
                
            keys = self.ui.get_input()
                
            if show_exit:
                if 'y' in keys or 'Y' in keys:
                    do_exit = True
                show_exit = False
                continue

            self.handle_input(size, keys)
            if 'window resize' in keys:
                size = self.ui.get_cols_rows()
            if 'q' in keys:
                show_exit = True
                do_exit = True
    
    def handle_input(self, size, keys):
        for k in keys:
            if urwid.is_mouse_event(k):
                event, button, col, row = k
                self.view.mouse_event( size, event,
                    button, col, row, focus=True )
            elif k != 'window resize':
                self.view.keypress( size, k )

def debug(msg):
    fd = file('/tmp/debug', 'a')
    fd.write(msg)
    fd.close()

def display(filelist, album, encoding):
    ot = OrderTracks(filelist, album, encoding)
    ot.main()
    return ot.tracks
