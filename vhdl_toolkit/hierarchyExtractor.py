from vhdl_toolkit.parser import Parser
from vhdl_toolkit.hdlObjects.reference import HdlRef
import multiprocessing
from multiprocess.pool import Pool
from python_toolkit.arrayQuery import arr_any
from vhdl_toolkit.hdlObjects.entity import Entity
from vhdl_toolkit.hdlObjects.package import PackageHeader
from vhdl_toolkit.hdlContext import HDLCtx
from vhdl_toolkit.nonRedefDict import RedefinitionErr


class DesignFile():
    """
    Wrapper around context of file
    """
    def __init__(self, fileName, hdlCtx):
        """
        @param fileName: filename of file that hdlCtx comes from
        @param hdlCtx: hdl context of file
        """
        self.fileName = fileName
        self.hdlCtx = hdlCtx
        self.importedNames = HDLCtx("imports", None)
        self.dependentOnFiles = set()

    @classmethod
    def fromFile(cls, f, libName='work', hdlCtx=None):
        """
        @param f: filename
        @param libName: library where context of the file will be placed if no
               hdlCtx is specified
        @param hdlCtx:  parent hdl context
        """
        return cls(f, Parser.parseFiles([f], Parser.VHDL, hdlCtx=hdlCtx, libName=libName,
                                timeoutInterval=180, hierarchyOnly=True))

    def allDefinedRefs(self):
        """
        iterate over all tuples (reference, referenced object)
        """
        def allDefinedRefsInCtx(ctx, nameList):
            for n, obj in ctx.items():
                if isinstance(obj, Entity):
                    yield (HdlRef(nameList + [n], False), obj)
                elif isinstance(obj, PackageHeader):
                    if not obj._isDummy:
                        yield (HdlRef(nameList + [n], False), obj)
                elif isinstance(obj, HDLCtx):
                    yield from allDefinedRefsInCtx(obj, nameList + [n])
        yield from allDefinedRefsInCtx(self.hdlCtx, [])

    def discoverImports(self, allDesignFiles, ignoredRefs=[]):
        """
        discover all imported names in design file
        """
        for d in self.allDependencies(importsOnly=True):
            if arr_any(ignoredRefs, lambda x: DesignFile.refMatch(d, x)):
                continue
            imp = DesignFile.findReference(d, allDesignFiles)
            if not imp:
                raise Exception("%s: require to import %s and it is not defined in any file" % 
                                (self.fileName, str(d)))
            if d.all:
                # imp_ref = imp[1]
                imp_obj = imp[2]
                try:
                    for k, v in imp_obj.items():
                        self.importedNames[k] = v
                except RedefinitionErr:
                    pass
            else:
                raise NotImplementedError()

    def allDependencies(self, importsOnly=False):
        """
        iterate all dependencies of file
        """
        def allDependenciesForCtx(ctx, nameList):
            # packageHeader < ent|arch|package
            # ent <- arch
            for _, obj in ctx.items():
                if isinstance(obj, Entity):
                    # components in packages does not have dependencies
                    if hasattr(obj, "dependencies"):
                        yield from obj.dependencies
                elif isinstance(obj, PackageHeader) and obj._isDummy:
                    yield HdlRef(nameList + [obj.name], False)
                elif isinstance(obj, HDLCtx):
                    for a in obj.architectures:
                        yield from a.dependencies
                        if not importsOnly:
                            yield HdlRef(nameList + [a.entityName], False)
                            for ci in a.componentInstances:
                                yield ci.entityRef
                    yield from allDependenciesForCtx(obj, nameList + [obj.name])
                # else:
                #    raise NotImplementedError(
                #          "Not implemented for object of type %s" %
                #           (obj.__class__.__name__))
        yield from allDependenciesForCtx(self.hdlCtx, [])

    @staticmethod
    def refMatch(iHad, iWontToHave):
        iwNames = iter(iWontToHave.names)
        ihNames = iter(iHad.names)
        # [TODO] not ideal solution will not work with other lib
        if iWontToHave.names[0] == 'work':
            next(iwNames)
        if iHad.names[0] == 'work':
            next(ihNames)
        for nh in ihNames:
            try:
                nw = next(iwNames)
            except StopIteration:
                return True
            if nh != nw:
                return False
            try:
                nw = next(iwNames)
            except StopIteration:
                return True

    @staticmethod
    def findReference(ref, allDesignFiles):
        """
        find reference in allDesignFiles
        @return: iterator over tuples (filename, reference, defined object)
        """
        for df in allDesignFiles:
                for defDep, obj in df.allDefinedRefs():
                    if DesignFile.refMatch(defDep, ref):
                        return (df.fileName, defDep, obj)

    def discoverDependentOnFiles(self, allDesignFiles, ignoredRefs=[]):
        """
        Discover on which files is this file dependent
        """
        def isAlreadyImported(ref):
            if len(ref.names) != 1:
                return False
            return ref.names[0] in self.importedNames

        self.discoverImports(allDesignFiles, ignoredRefs=ignoredRefs)
        for d in self.allDependencies():
            if arr_any(ignoredRefs, lambda x: DesignFile.refMatch(d, x)):
                continue
            if isAlreadyImported(d):
                continue
            df = self.findReference(d, allDesignFiles)
            if not df:
                raise Exception(
                 "%s: require to import %s and it is not defined in any file" % 
                 (self.fileName, str(d)))
            self.dependentOnFiles.add(df[0])

    @staticmethod
    def loadFiles(files, libName='work', parallel=True):
        if parallel:
            with Pool(multiprocessing.cpu_count()) as pool:
                designFiles = pool.map(
                                lambda f: DesignFile.fromFile(f, libName=libName),
                                files)
        else:
            designFiles = []
            for f in files:
                d = DesignFile.fromFile(f, libName=libName)
                designFiles.append(d)
        return designFiles

    @staticmethod
    def fileDependencyDict(designFiles, ignoredRefs=[HdlRef(["ieee"], False)]):
        depDict = {}
        for df in designFiles:
            df.discoverDependentOnFiles(designFiles, ignoredRefs)
            depDict[df.fileName] = df.dependentOnFiles
        return depDict


def findFileWhereNameIsDefined(designFiles, name):
    targetRef = HdlRef([name])
    for df in designFiles:
        refs = df.allDefinedRefs()
        for ref in refs:
            if DesignFile.refMatch(ref, targetRef):
                return df
