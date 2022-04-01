import time
from threading import Lock

# region PRINT_FUNCTION
print_sync_lock = Lock()
last_print_length = 0
last_printed_prompt_length = 0


def get_default_print_sync_lock() -> Lock:
    """Provides module's default <threading.Lock> object used to synchronize print function.
    :rtype: threading.Lock default print synchronization Lock object.
    """
    return print_sync_lock


def print_single_line(*s, end=''):
    global last_print_length, last_printed_prompt_length
    with print_sync_lock:
        joined_s = ', '.join([str(x) for x in s])
        print(chr(8) * (last_print_length + last_printed_prompt_length) + joined_s, end=end)
        # last_print_length = len(joined_s) if '\n' not in end else 0  # 대개는 문제 없지만 바이트 길이의 영향을 받는 경우 문제가 생김.
        last_printed_prompt_length = 0
        last_print_length = len(joined_s.encode()) if '\n' not in end else 0


def progress(
        o, step: int = -1, milestones: int = 0, name: str = '', print_in_single_line=True, print_elapsed_time=False,
        line_feed_on_stop=True):
    """
    Create a generator to print progress of iteration.

    :param o: object to be yielded by generator.
    :param step: int steps between printing progress. Negative value changes into length of 'o'.
    :param milestones: int 'milestones' such that greater than 0, print progress (at most) 'milestones' times.
    :param name: str additional name to show currently iterating object 'o'.
    :param print_in_single_line: bool if True, try to use single line to print progress. See Also, 'print_single_line()'
    :param print_elapsed_time: bool if True, print elapsed time since this generator works.
    :param line_feed_on_stop: bool if True, last printing message will be line fed,
    regardless of printing in single line or not.
    :return:
    """
    print_function = print_single_line if print_in_single_line else print  # TODO
    _len = 1  # For non-iterable object
    name = f': {name}' if name != '' else '.'
    _start_time = time.time()
    try:
        _len = len(o)
        if milestones > 0:
            step = _len // milestones
        if step == 0:
            step = 1  # Case such as 'milestones' > 'len(o)'
        elif step < 0:
            step = _len
        _string_format_with_width = f'Iteration Progressing..{{}} [{{:>{len(str(_len))}}}/{{}}]'
        for _i, _o in enumerate(o):
            if _i % step == 0:
                _elapsed_time = ' {:.3f}s'.format(time.time() - _start_time) if print_elapsed_time else ''
                print_function(_string_format_with_width.format(name, _i, _len) + _elapsed_time)
            yield _o
    except TypeError:
        yield o  # Case of non-iterable object
    finally:
        _elapsed_time = ' {:.3f}s'.format(time.time() - _start_time) if print_elapsed_time else ''
        # progress.generator_running_time = _elapsed_time  # NOTE - not thread safe.
        print_function(
            'Iteration Completed{0:}    [{1:}/{1:}]'.format(name, _len) + _elapsed_time,
            end='' if print_in_single_line and not line_feed_on_stop else '\n')
# endregion PRINT_FUNCTION
