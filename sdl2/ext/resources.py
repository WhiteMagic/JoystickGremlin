"""
Resource management methods.
"""
import sys
import os
import re
import zipfile
import tarfile
import io

__all__ = ["open_zipfile", "open_tarfile", "open_url", "Resources"]

# Python 3.x workarounds for the changed urllib modules.
if sys.version_info[0] >= 3:
    import urllib.parse as urlparse
    import urllib.request as urllib2
else:
    import urlparse
    import urllib2


def open_zipfile(archive, filename, directory=None):
    """Opens and reads a certain file from a ZIP archive.

    Opens and reads a certain file from a ZIP archive. The result is
    returned as StringIO stream. filename can be a relative or absolute
    path within the ZIP archive. The optional directory argument can be
    used to supply a relative directory path, under which filename will
    be searched.

    If the filename could not be found, a KeyError will be raised.
    Raises a TypeError, if archive is not a valid ZIP archive.
    """
    data = None
    opened = False

    if not isinstance(archive, zipfile.ZipFile):
        if not zipfile.is_zipfile(archive):
            raise TypeError("passed file does not seem to be a ZIP archive")
        else:
            archive = zipfile.ZipFile(archive, 'r')
            opened = True

    apath = filename
    if directory:
        apath = "%s/%s" % (directory, filename)

    try:
        dmpdata = archive.open(apath)
        data = io.BytesIO(dmpdata.read())
    finally:
        if opened:
            archive.close()
    return data


def open_tarfile(archive, filename, directory=None, ftype=None):
    """Opens and reads a certain file from a TAR archive.

    Opens and reads a certain file from a TAR archive. The result is
    returned as StringIO stream. filename can be a relative or absolute
    path within the TAR archive. The optional directory argument can be
    used to supply a relative directory path, under which filename will
    be searched.

    ftype is used to supply additional compression information, in case
    the system cannot determine the compression type itself, and can be
    either 'gz' for gzip compression or 'bz2' for bzip2 compression.

    Note:

      If ftype is supplied, the compression mode will be enforced for
      opening and reading.

    If the filename could not be found or an error occured on reading it,
    None will be returned.

    Raises a TypeError, if archive is not a valid TAR archive or if type
    is not a valid value of ('gz', 'bz2').
    """
    data = None
    opened = False

    mode = 'r'
    if ftype:
        if ftype not in ('gz', 'bz2'):
            raise TypeError("invalid TAR compression type")
        mode = "r:%s" % ftype

    if not isinstance(archive, tarfile.TarFile):
        if not tarfile.is_tarfile(archive):
            raise TypeError("passed file does not seem to be a TAR archive")
        else:
            archive = tarfile.open(archive, mode)
            opened = True

    apath = filename
    if directory:
        apath = "%s/%s" % (directory, filename)

    try:
        dmpdata = archive.extractfile(apath)
        data = io.BytesIO(dmpdata.read())
    finally:
        if opened:
            archive.close()
    return data


def open_url(filename, basepath=None):
    """Opens and reads a certain file from a web or remote location.

    Opens and reads a certain file from a web or remote location. This
    function utilizes the urllib2 module, which means that it is
    restricted to the types of remote locations supported by urllib2.

    basepath can be used to supply an additional location prefix.
    """
    url = filename
    if basepath:
        url = urlparse.urljoin(basepath, filename)
    return urllib2.urlopen(url)


class Resources(object):
    """The Resources class manages a set of file resources and eases
    accessing them by using relative paths, scanning archives
    automatically and so on.
    """
    def __init__(self, path=None, subdir=None, excludepattern=None):
        """Creates a new resource container instance.

        If path is provided, the resource container will scan the path
        and add all found files to itself by invoking
        scan(path, subdir, excludepattern).
        """
        self.files = {}
        if path:
            self.scan(path, subdir, excludepattern)

    def _scanzip(self, filename):
        """Scans the passed ZIP archive and indexes all the files
        contained by it.
        """
        if not zipfile.is_zipfile(filename):
            raise TypeError("file '%s' is not a valid ZIP archive" % filename)
        archname = os.path.abspath(filename)
        zipf = zipfile.ZipFile(filename, 'r')
        for path in zipf.namelist():
            fname = os.path.split(path)[1]
            if fname:
                self.files[fname] = (archname, 'zip', path)
        zipf.close()

    def _scantar(self, filename, ftype=None):
        """Scans the passed TAR archive and indexes all the files
        contained by it.
        """
        if not tarfile.is_tarfile(filename):
            raise TypeError("file '%s' is not a valid TAR archive" % filename)
        mode = 'r'
        if ftype:
            if ftype not in ('gz', 'bz2'):
                raise TypeError("invalid TAR compression type")
            mode = "r:%s" % ftype
        archname = os.path.abspath(filename)
        archtype = 'tar'
        if ftype:
            archtype = 'tar%s' % ftype
        tar = tarfile.open(filename, mode)
        for path in tar.getnames():
            fname = os.path.split(path)[1]
            self.files[fname] = (archname, archtype, path)
        tar.close()

    def add(self, filename):
        """Adds a file to the Resources container.

        Depending on the file type (determined by the file suffix or name),
        the file will be automatically scanned (if it is an archive) or
        checked for availability (if it is a stream/network resource).
        """
        if not os.path.exists(filename):
            raise ValueError("invalid file path")
        if zipfile.is_zipfile(filename):
            self.add_archive(filename)
        elif tarfile.is_tarfile(filename):
            self.add_archive(filename, 'tar')
        else:
            self.add_file(filename)

    def add_file(self, filename):
        """Adds a file to the Resources container.

        This will only add the passed file and do not scan an archive or
        check a stream for availability.
        """
        if not os.path.exists(filename):
            raise ValueError("invalid file path")
        abspath = os.path.abspath(filename)
        fname = os.path.split(abspath)[1]
        if not fname:
            raise ValueError("invalid file path")
        self.files[fname] = (None, None, abspath)

    def add_archive(self, filename, typehint='zip'):
        """Adds an archive file to the Resources container.

        This will scan the passed archive and add its contents to the
        list of available resources.
        """
        if not os.path.exists(filename):
            raise ValueError("invalid file path")
        if typehint == 'zip':
            self._scanzip(filename)
        elif typehint == 'tar':
            self._scantar(filename)
        elif typehint == 'tarbz2':
            self._scantar(filename, 'bz2')
        elif typehint == 'targz':
            self._scantar(filename, 'gz')
        else:
            raise ValueError("unsupported archive type")

    def get(self, filename):
        """Gets a specific file from the Resources.

        Raises a KeyError, if filename could not be found.
        """
        archive, ftype, pathname = self.files[filename]
        if archive:
            if ftype == 'zip':
                return open_zipfile(archive, pathname)
            elif ftype == 'tar':
                return open_tarfile(archive, pathname)
            elif ftype == 'tarbz2':
                return open_tarfile(archive, pathname, ftype='bz2')
            elif ftype == 'targz':
                return open_tarfile(archive, pathname, ftype='gz')
            else:
                raise ValueError("unsupported archive type")
        dmpdata = open(pathname, 'rb')
        data = io.BytesIO(dmpdata.read())
        dmpdata.close()
        return data

    def get_filelike(self, filename):
        """Like get(), but tries to return the original file handle, if
        possible.

        If the passed filename is only available within an archive, a
        StringIO instance will be returned.

        Raises a KeyError, if filename could not be found.
        """
        archive, ftype, pathname = self.files[filename]
        if archive:
            if ftype == 'zip':
                return open_zipfile(archive, pathname)
            elif ftype == 'tar':
                return open_tarfile(archive, pathname)
            elif ftype == 'tarbz2':
                return open_tarfile(archive, pathname, ftype='bz2')
            elif ftype == 'targz':
                return open_tarfile(archive, pathname, ftype='gz')
            else:
                raise ValueError("unsupported archive type")
        return open(pathname, 'rb')

    def get_path(self, filename):
        """Gets the path of the passed filename.

        If filename is only available within an archive, a string in
        the form 'filename@archivename' will be returned.

        Raises a KeyError, if filename could not be found.
        """
        archive, ftype, pathname = self.files[filename]
        if archive:
            return '%s@%s' % (pathname, archive)
        return pathname

    def scan(self, path, subdir=None, excludepattern=None):
        """Scans a path and adds all found files to the Resources
        container.

        Scans a path and adds all found files to the Resources
        container. If a file is a supported (ZIP or TAR) archive, its
        contents will be indexed and added automatically.

        The method will consider the directory part (os.path.dirname) of
        the provided path as path to scan, if the path is not a
        directory. If subdir is provided, it will be appended to the
        path and used as starting point for adding files to the
        Resources container.

        excludepattern can be a regular expression to skip directories, which
        match the pattern.
        """
        match = None
        if excludepattern:
            match = re.compile(excludepattern).match
        join = os.path.join
        add = self.add
        abspath = os.path.abspath(path)
        if not os.path.exists(abspath):
            raise ValueError("invalid path '%s'" % path)
        if not os.path.isdir(abspath):
            abspath = os.path.dirname(abspath)
        if subdir is not None:
            abspath = os.path.join(abspath, subdir)
        if not os.path.exists(abspath):
            raise ValueError("invalid path '%s'" % path)
        for (pdir, dirnames, filenames) in os.walk(abspath):
            if match and match(pdir) is not None:
                continue
            for fname in filenames:
                add(join(pdir, fname))
