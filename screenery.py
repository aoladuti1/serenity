"""SCREENERY - by Antonio Oladuti.\n
This library is okay, I guess. It's just kind of nichely useful.
If you find yourself needing a lot of information about screen dimensions
and co-ordinates, you will save a lot of time
by using these functions. Many online solutions have been weird, annoying
convoluted, or some mix of the three. Why do you think I put this together?

The motivation of this library was to abstract away problems
that come part-and-parcel with things such as Apple Retina
displays, DPI Scaling, Windows being Windows, multi-monitor setups, and
the pain of programming.

This module can be integrated quite well with tkinter (by design),
and somewhat well with PyQt.

Note that the Monitor objects will ACCURATELY report the fluctuating
(apparent) change in resolution of a display
when it is in a multi-monitor setup.

The constant 'DPR' is the device pixel ratio.

The import 'info' is an alias for the wonderful screeninfo module.

Screenery is cross-platform! Yatta."""


import screeninfo as info
import pyautogui
import sys as _sys
import math as _math
import tkinter as _tk
import ctypes as _ctypes
import cython as _cython  # for mac OSX screeninfo compatability
from screeninfo import Monitor
from PyQt5.QtWidgets import QApplication as _QApplication
from PyQt5.QtWidgets import QDesktopWidget as _QDesktopWidget

if _sys.platform in ('win32', 'darwin'):
    try:  # windows >= 8.1
        _ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:  # windows <= 8.0
        _ctypes.windll.user32.SetProcessDPIAware()

DPR = pyautogui.screenshot().size[0]/pyautogui.size().width  # DevicePixelRatio


# called to ensure DPR adjustment for some methods, with whole pixels returned
def __DPR_ceil(x: int, y):
    return (_math.ceil(x / DPR), _math.ceil(y / DPR))


def title_bar_height(
        window: _tk.Toplevel = None, maximised: bool = False) -> int:
    """Returns the height of the title bar in pixels for the primary monitor.
    Calling this function comes with many potential side-effects.

    Call once if possible, and only before a Tk() call,
    if window is None. This is because the function will call Tk() again
    if window isn't specified, and windows will hide themselves annoyingly.

    Note: if window is None, this function call may cause one
    inescapable flicker on the screen, due to the mandatory Tk() call.

    Args:
        maximised (bool, optional): if True returns the height of a
        maximised window's title bar. Otherwise, the height of a normal,
        unzoomed window is returned. BUT, if a window is specified, then this
        function will return the height of the title bar
        for whatever state window is in. Only works on Microsoft Windows.
        Defaults to False.
        window (Toplevel, optional): if specified, the flicker caused by
        creating a new Tk() instance can be avoided,
        and this function will use the tkinter window provided to return
        the title bar height. Defaults to None.

    Returns:
        int: the height of the title bar in pixels
    """
    # Inspired by an answer from Daniel Huckson @StackOverflow
    if window is not None:
        return __get_tbh_from_window(window)
    app = _tk.Tk()  # draw app
    app.attributes('-alpha', 0)
    app.geometry('0x0+0+0')
    if maximised is True:
        app.state('zoomed')
    app.update()
    _tk.Frame(app).update_idletasks()
    app.update_idletasks()
    offset_y = 0
    if _sys.platform in ('win32', 'darwin'):
        offset_y = int(app.geometry().rsplit('+', 1)[-1])
    height = app.winfo_rooty() - offset_y
    app.destroy()
    return height if height > 0 else 0


def __get_tbh_from_window(window: _tk.Toplevel) -> int:
    window.update()
    f = _tk.Frame(window)
    f.update_idletasks()
    window.update_idletasks()
    offset_y = 0
    if _sys.platform in ('win32', 'darwin'):
        offset_y = int(window.geometry().rsplit('+', 1)[-1])
    height = window.winfo_rooty() - offset_y
    f.destroy()
    return height if height > 0 else 0


def monitors() -> list[Monitor]:
    """Returns a list of Monitor objects for all monitors
    connected to this _system.

    Returns:
        list[Monitor]: a list of Monitor objects for all connected
        monitors to this _system
    """
    return info.get_monitors()


def mouse_coords() -> tuple[int, int]:
    """Returns an (x, y) tuple for the coordinates of the mouse pointer, where
    x and y are the respective horizontal and vertical pixel distances
    from the top left corner of the primary monitor.


    Returns:
        tuple[int, int]: _description_
    """
    pos = pyautogui.position()
    return __DPR_ceil(pos.x, pos.y)


# I love this
def test_mouse_and_RGB():
    """This function is meant to be run from the command line. It will
    automatically display the location and RGB of the mouse cursor.
    X and Y may be inaccurate for Retina displays."""
    pyautogui.displayMousePosition()


def mouse_monitor() -> tuple[int, int]:
    x, y = mouse_coords()
    return monitor_from_coords(x, y)


def tuplefy_coord(x: int = None, y: int = None) -> tuple[int, int]:
    """Takes x or y as a pixel coordinate. If there is a non-specified
    coordinate, it is returned as 0 in a tuple of (x, y) pixel coordinates.

    Args:
        x (int, optional): the x coordinate. Defaults to None.
        y (int, optional): the y coordinate. Defaults to None.

    Returns:
        tuple[int, int]: a tuple of x and y pixel coordinates/dimensions,
        in which the non-specified coordinate is 0 in the returned tuple.
    """
    if x is not None:
        return (x, 0) if y is None else (x, y)
    if y is not None:
        return (0, y) if x is None else (x, y)
    return (0, 0)


def available_geometry(
        desktop: _QDesktopWidget = None) -> tuple[int, int]:
    """Returns the available (unreserved) geometry of the
    primary monitor as a tuple of width and height in pixels.

    Args:
        desktop (QDesktopWidget, optional): if None, a new QApplication and
        QDesktopWidget will be generated.

    Returns:
        tuple: (width, height) in pixels
    """
    if desktop is None:
        app = _QApplication(_sys.argv)
        geometry = app.desktop().availableGeometry()
    else:
        geometry = desktop.availableGeometry()
    return __DPR_ceil(geometry.width(), geometry.height())


def reserved_geometry(
        desktop: _QDesktopWidget = None) -> tuple[int, int]:
    """Returns the reserved (unavailable) geometry of the
    primary monitor as a tuple of width and height in pixels.
    An example of a reserved space would be the task bar.


    Args:
        desktop (QDesktopWidget, optional): if None, a new QApplication and
        QDesktopWidget will be generated.

    Returns:
        tuple: (width, height) in pixels
    """
    if desktop is None:
        app = _QApplication(_sys.argv)
        dw = app.desktop()
    else:
        dw = desktop
    geometry = dw.screenGeometry()
    all_width = geometry.width()
    all_height = geometry.height()
    l_width, l_height = available_geometry(dw)
    return __DPR_ceil(all_width - l_width, all_height - l_height)


def widget_monitor_geometry(widget: _tk.Widget) -> tuple[int, int]:
    """Returns the geometry of the monitor displaying the specified widget
    as an (x, y) tuple of dimensions. If the widget is not located, the
    returned value will be for the primary monitor.

    Args:
        monitor (Monitor, optional): the monitor selected. Defaults to None.

    Returns:
        tuple[int, int]: the geometry of the primary monitor
    """
    try:
        m = monitor_from_coords(widget.winfo_x(), widget.winfo_y())
    except Exception:
        m = primary_geometry()
    finally:
        return (m.width, m.height)


def widget_monitor(widget: _tk.Widget) -> Monitor:
    """Returns a Monitor object for the monitor that is currently
    displaying the specified Tkinter widget, or the primary monitor
    if the widget was not located.

    Args:
        widget (Tk): the widget to locate

    Returns:
        Monitor: the Monitor object for the monitor displaying the widget
    """
    try:
        return monitor_from_coords(widget.winfo_x(), widget.winfo_y())
    except Exception:
        return primary_monitor()


def monitor_from_coords(x: int, y: int) -> Monitor:
    """Returns a Monitor for the monitor displaying the x and y pixel
    coordinates of a visual object on the screen, if such a monitor
    exists. Failing this, a Monitor object for the
    primary monitor is returned instead.

    Note: x and y are horizontal and vertical the respective pixel distances
    from the top-left corner of the primary monitor.

    Args:
        x (int): x coordinate (in pixels)
        y (int): y coordinate (in pixels)

    Returns:
        Monitor: the Monitor object associated to the monitor displaying
        the passed coordinates.
    """
    # Lifted from an answer by ThenTech @StackOverflow
    monitors = info.get_monitors()
    for m in reversed(monitors):
        if m.x <= x <= m.width + m.x and m.y <= y <= m.height + m.y:
            return m
    return monitors[0]


def primary_monitor() -> Monitor:
    """Return the Monitor object for this system's primary monitor.

    Returns:
        Monitor: the primary monitor object
    """
    return monitors()[0]


def primary() -> Monitor:
    """Return the Monitor object for this system's primary monitor.

    Returns:
        Monitor: the primary monitor object
    """
    return monitors()[0]


def monitor_count() -> int:
    """Returns the number of monitors for this system.

    Returns:
        int: number of monitors
    """
    return len(monitors())


def monitor_geometry(monitor: Monitor) -> tuple[int, int]:
    """Returns the geometry of a monitor as a
    (width, height) tuple of pixel lengths.

    Args:
        monitor (Monitor): the Monitor object for a chosen monitor

    Returns:
        tuple[int, int]: the geometry of the specified monitor
    """
    return (monitor.width, monitor.height)


def primary_monitor_geometry():
    """Returns the geometry of the primary monitor as a
    (width, height) tuple of pixel lengths.

    Args:
        monitor (Monitor): the Monitor object for a chosen monitor

    Returns:
        tuple[int, int]: the geometry of the primary monitor
    """
    return monitor_geometry(primary_monitor())


def primary_geometry():
    """Returns the geometry of the primary monitor as a
    (width, height) tuple of pixel lengths.

    Args:
        monitor (Monitor): the Monitor object for a chosen monitor

    Returns:
        tuple[int, int]: the geometry of the primary monitor
    """
    return monitor_geometry(primary_monitor())


def nicely_print(monitor: Monitor):
    """Nicely prints Monitor object attribute names and values.

    Args:
        monitor (Monitor): the monitor object to nicely print out
    """
    print("---------------------\n")
    for k, v in vars(monitor).items():
        print(k, "=", v)
    print("---------------------")
