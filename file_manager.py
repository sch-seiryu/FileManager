# <IMPORT>  # [<USED_REGION,...>]
import os  # [Comparison,]
import time  # [Comparison,]

from utils import progress

# region Functional

# endregion Functional


# region Comparison
FILE_SIZE_LIMIT_GIB = 64
GIB = 1_073_741_824  # = 1024 ** 3
BITWISE_COMPARISON_THRESHOLDS = ('match', 'compare', 'difference')


def bitwise_comparison(dir1, dir2, buffer_size=8192, threshold='match', intensity=1., file_name=''):
    # TODO 'dir3'을 없앤 대신, 그것을 미리 정제하는 과정이 호출 전에 불러진다고 가정함. 결합도를 낮추고 파라미터를 명확하게 하기 위함.
    # dir1: 1번 파일 절대 경로
    # dir2: 2번 파일 절대 경로
    # 'intensity'는 작업 강도를 정하는것. 값을 낮춰 파일을 읽는 시간 비중을 줄여서 과도한 자원 사용을 막을 수 있다.
    # (특히 작업 시간이 긴 경우를 고려하기 위함)
    # 기준은 읽기 200회당 무휴 시간 비율로 정한다. -> 버퍼 크기에 따라 가변적으로 조정함. 일단 50KiB 기준으로 나눔.
    #
    # 반환: 동일시 동일 길이, 차이시 차이 길이?, 차이시 차이 부분?
    # match: 일치, 처음 다른 지점 반환
    # compare: 일치하지 않는 모든 구간을 반환
    # difference: 동일 시퀸스를 찾아 보여주기
    # 참고로 용어는 미정. compare랑 difference를 바꾸는 게 맞는거 같기도 하고 등등해서 확정된 부분은 아님.
    # 매개변수값 목록
    if threshold not in BITWISE_COMPARISON_THRESHOLDS:
        raise KeyError(f'The given threshold value \'{threshold}\' is not defined.')
    elif threshold is not 'match':  # 'difference':
        raise NotImplementedError()

    # 작업 강도값 확인
    INTENSITY_CYCLE = [20, 200][buffer_size <= 524_288]  # 50KiB
    take_break_at = 0
    idling_coef = 0.
    if 0 < intensity < 1.:
        take_break_at = int(INTENSITY_CYCLE * intensity)
        # 하한선 문제 발생 대비
        if take_break_at <= 0:
            take_break_at = 1
        idling_coef = (INTENSITY_CYCLE - take_break_at) / take_break_at
    else:
        raise ValueError('Intensity must be within the range of 0 < intensity <= 1.f')

    len1, len2 = 0, 0
    diff = []

    use_file_size_not_maximum_gib = True
    step_limit: int
    if use_file_size_not_maximum_gib:
        # OS에 의해 반환된 크기 -> 목적에 따라선 여기서 단순히 크기가 다른 경우를 골라내도 상관은 없다.
        size1, size2 = os.stat(dir1).st_size, os.stat(dir2).st_size
        target_size = size1 if size1 >= size2 else size2
    else:
        # 버퍼 크기 기준, 최대 파일 사이즈까지의 조각 수
        target_size = FILE_SIZE_LIMIT_GIB * GIB
    step_limit, r = divmod(target_size, buffer_size)
    if r:
        step_limit += 1
    # 진행도 출력할 크기(메가바이트 단위)
    mib_to_print = 100
    steps_to_print = (1024 ** 2) * mib_to_print // buffer_size
    # 현재 작업중인 파일 이름 출력(옵션)
    MAX_DISPLAY_LENGTH = 30  # 글자 수 제한(확장자 제외)
    MAX_EXTENSION_LENGTH = 8  # 확장자명의 길이 한계
    file_name_to_display = ''  # (한편으로는) 디폴트 값으로 초기화해둠('progress'로 전달할때)
    if file_name:
        name_only, extension = file_name, ''
        # 확장자가 존재하는 경우(아닐 수도 있음)
        if '.' in file_name:
            extension_pivot_index = file_name.rfind('.')
            if 0 < len(file_name) - extension_pivot_index - 1 <= MAX_EXTENSION_LENGTH:
                name_only, extension = file_name[:extension_pivot_index], file_name[extension_pivot_index+1:]

        if len(name_only) > MAX_DISPLAY_LENGTH:
            if extension:
                file_name_to_display = name_only[:MAX_DISPLAY_LENGTH - 5] + ' ... .' + extension
            else:
                file_name_to_display = name_only[:MAX_DISPLAY_LENGTH - 4] + ' ...'
        else:
            file_name_to_display = file_name

    last_time = time.time()
    with open(dir1, 'rb') as f1, open(dir2, 'rb') as f2:
        # if threshold != 'difference':
        # while True:
        for k in progress(range(step_limit), name=file_name_to_display, step=steps_to_print, print_elapsed_time=True):
            # 작업 강도를 줄일 경우, 걸린 시간을 기준으로 휴식을 취함.
            if take_break_at:
                if k > 0 and k % take_break_at:
                    # 작업 정지
                    time.sleep((time.time() - last_time) * idling_coef)
                    # 재개 시간 업데이트
                    last_time = time.time()

            r1 = f1.read(buffer_size)
            r2 = f2.read(buffer_size)
            # print('\n', r1[:20], '\n', r2[:20])

            if len(r1) is 0 and len(r2) is 0:
                break
            if len(r1):
                len1 += buffer_size if len(r1) == buffer_size else len(r1)
            if len(r2):
                len2 += buffer_size if len(r2) == buffer_size else len(r2)

            # file size are different
            if len(r1) != len(r2):
                return 'have different size', len1, len2  # TODO different len
            # no problem in this section
            elif r1 == r2:
                continue
            # found different pattern
            else:
                eq = True
                if threshold == 'match':
                    for idx, (b1, b2) in enumerate(zip(r1, r2)):
                        if b1 != b2:
                            return 'byte sequence difference at', (len1 - buffer_size + idx + 1), b1, b2

    # 일치시 문자열 'match'와 함께 두 파일의 크기를 반환한다. 이 때 os가 제공한 크기와 일치하는지 체크할 수도 있겠다.
    return 'match', len1
# endregion


# region Selection # TODO +FileSystem?
class Entity:
    """Base class for both files and directories.

    """

    def __init__(self, name):
        self.name = name
        self.counts = 1  # When it comes to a file, its count is definitely 1. Only counts # of files.


class File(Entity):

    def __init__(self, name, extension):
        super().__init__(name)

        self.extension = extension


class Folder(Entity):

    def __init__(self, name, files):
        super().__init__(name)

        self.files = files or []
        self.counts = len(self.files)

    @DeprecationWarning
    def refresh(self):
        self.counts = len(self.files)


@NotImplemented
class Identity:
    """우리가 취급할 때 '동일하다'고 생각되는 대상을 지칭하고자 함. 멤버로 <File> objects 또는 <Folder> objects 사용.

    """
    pass


class Select:
    """A tree structure data to highlight selected files, and directory hierarchies.
    Search algorithms should be designed using 'depth-first-search', rather than 'breadth-first-search'.
    In short, each 'Select' object represents a directory, and its search algorithms are biased on DFS.
    """

    def __init__(self, parent, path: str, entity: dict):
        self.parent = parent
        self.path = path if parent is None else os.path.join(parent.path, path)
        self.entity = entity  # <K, V> = <name: str, extension: str>, and a specific extension <'.'> for directories.
        # _ [POTENTIAL_WARNING] Directory extension('.') possibly cause malfunction on Non-Windows OS file systems.

    @staticmethod
    def create_select_root(path: str, entity: dict):
        return Select(None, path, entity)

    @property
    def is_root(self):
        return self.parent is None

    @staticmethod
    def take_files(dir1, dir2, select=(), ignore=()):
        # 유의 사항
        # 1. 동일 파일명만 탐색. 접두사와 접미사, 또는 특정 포멧을 만족하는 파일을 한 쌍으로 인식하는 부분은 구현되지 않음.
        # 2. 하위 디렉터리는 검사하지 않음.
        # 3. 여러 폴더에 나뉘어 있거나, 동일 폴더 내에 존재하는 사본 파일에 대한 탐색을 지원하지 않음.
        # 4. 반환값은 일치하는 각각의 파일명이지 전체 경로나 상대 경로가 아니다.
        # select: 사용할 파일명 한정
        # ignore: 사용하지 않을 파일명 지정
        l1, l2 = os.listdir(dir1), os.listdir(dir2)

        # 합집합 구하기
        s = set(l1).intersection(set(l2))
        # 특정 파일만 구하고자 하는 경우.
        dropped = None
        if select:
            select = set(select)
            dropped = select - s
            if dropped:
                dropped = sorted(list(dropped))
            s = s.intersection(select)
        # 특정 파일을 제외하고자 하는 경우.
        if ignore:
            s = s.difference(set(ignore))
        # 이름순 재정렬
        l = sorted(list(s))
        # 디렉터리는 제외하고 파일명만 수집(경로명은 합치지 않고, 파일명만 리스팅한다)
        l = [x for x in l if not (os.path.isdir(os.path.join(dir1, x)) or os.path.isdir(os.path.join(dir2, x)))]
        return l, dropped
# endregion Select


if __name__ == '__main__':
    print(f"Comparison finished at {time.strftime('%Y-%m-%d %H:%M:%S')}")  # TODO
