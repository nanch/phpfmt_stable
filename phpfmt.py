import csv
import os
import os.path
import shutil
import sublime
import sublime_plugin
import subprocess
import time
import sys
from os.path import dirname, realpath

dist_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, dist_dir)
from diff_match_patch.python3.diff_match_patch import diff_match_patch

def print_debug(*msg):
     if getSetting(sublime.active_window().active_view(), sublime.load_settings('phpfmt.sublime-settings'), "debug", False):
        print(msg)

def getSetting( view, settings, key, default ):
    local = 'phpfmt.' + key
    return view.settings().get( local, settings.get( key, default ) )

def dofmt(eself, eview, sgter = None, src = None, force = False):
    if int(sublime.version()) < 3000:
        print_debug("phpfmt: ST2 not supported")
        return False

    self = eself
    view = eview
    s = sublime.load_settings('phpfmt.sublime-settings')


    additional_extensions = getSetting( view, s, "additional_extensions", [])
    autoimport = getSetting( view, s, "autoimport", True)
    debug = getSetting( view, s, "debug", False)
    enable_auto_align = getSetting( view, s, "enable_auto_align", False)
    ignore_list = getSetting( view, s, "ignore_list", "")
    indent_with_space = getSetting( view, s, "indent_with_space", False)
    psr1 = getSetting( view, s, "psr1", False)
    psr1_naming = getSetting( view, s, "psr1_naming", psr1)
    psr2 = getSetting( view, s, "psr2", False)
    smart_linebreak_after_curly = getSetting( view, s, "smart_linebreak_after_curly", True)
    skip_if_ini_missing = getSetting( view, s, "skip_if_ini_missing", False)
    visibility_order = getSetting( view, s, "visibility_order", False)
    yoda = getSetting( view, s, "yoda", False)
    readini = getSetting( view, s, "readini", False)

    passes = getSetting( view, s, "passes", [])
    excludes = getSetting( view, s, "excludes", [])

    php_bin = getSetting( view, s, "php_bin", "php")
    formatter_path = os.path.join(dirname(realpath(sublime.packages_path())), "Packages", "phpfmt", "fmt.phar")

    config_file = os.path.join(dirname(realpath(sublime.packages_path())), "Packages", "phpfmt", "php.tools.ini")

    uri = view.file_name()
    dirnm, sfn = os.path.split(uri)
    ext = os.path.splitext(uri)[1][1:]

    if force is False and "php" != ext and not ext in additional_extensions:
        print_debug("phpfmt: not a PHP file")
        return False

    if "" != ignore_list:
        if type(ignore_list) is not list:
            ignore_list = ignore_list.split(" ")
        for v in ignore_list:
            pos = uri.find(v)
            if -1 != pos and v != "":
                print_debug("phpfmt: skipping file")
                return False

    if not os.path.isfile(php_bin) and not php_bin == "php":
        print_debug("Can't find PHP binary file at "+php_bin)
        sublime.error_message("Can't find PHP binary file at "+php_bin)

    # Look for oracle.sqlite
    if dirnm != "":
        oracleDirNm = dirnm
        while oracleDirNm != "/":
            oracleFname = oracleDirNm+os.path.sep+"oracle.sqlite"
            if os.path.isfile(oracleFname):
                break
            origOracleDirNm = oracleDirNm
            oracleDirNm = os.path.dirname(oracleDirNm)
            if origOracleDirNm == oracleDirNm:
                break

        if not os.path.isfile(oracleFname):
            print_debug("phpfmt (oracle file): not found")
            oracleFname = None
        else:
            print_debug("phpfmt (oracle file): "+oracleFname)

        if readini:
            iniDirNm = dirnm
            while iniDirNm != "/":
                iniFname = iniDirNm+os.path.sep+".php.tools.ini"
                if os.path.isfile(iniFname):
                    break
                originiDirNm = iniDirNm
                iniDirNm = os.path.dirname(iniDirNm)
                if originiDirNm == iniDirNm:
                    break

            if os.path.isfile(iniFname):
                print_debug("phpfmt (ini file): "+iniFname)
                config_file = iniFname
            elif skip_if_ini_missing:
                print_debug("phpfmt (ini file): not found - skipping")
                return False
    else:
        oracleFname = None

    cmd_ver = [php_bin, '-v'];
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        p = subprocess.Popen(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, startupinfo=startupinfo)
    else:
        p = subprocess.Popen(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    res, err = p.communicate()
    print_debug("phpfmt (php_ver) cmd:\n", cmd_ver)
    print_debug("phpfmt (php_ver) out:\n", res.decode('utf-8'))
    print_debug("phpfmt (php_ver) err:\n", err.decode('utf-8'))
    if ('PHP 5.3' in res.decode('utf-8') or 'PHP 5.3' in err.decode('utf-8') or 'PHP 5.4' in res.decode('utf-8') or 'PHP 5.4' in err.decode('utf-8') or 'PHP 5.5' in res.decode('utf-8') or 'PHP 5.5' in err.decode('utf-8') or 'PHP 5.6' in res.decode('utf-8') or 'PHP 5.6' in err.decode('utf-8')):
        s = debugEnvironment(php_bin, formatter_path)
        sublime.message_dialog('Warning.\nPHP 7.0 or newer is required.\nPlease, upgrade your local PHP installation.\nDebug information:'+s)
        return False

    s = debugEnvironment(php_bin, formatter_path)
    print_debug(s)

    lintret = 1
    if "AutoSemicolon" in passes:
        lintret = 0
    else:
        cmd_lint = [php_bin,"-ddisplay_errors=1","-l"];
        if src is None:
            cmd_lint.append(uri)
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                p = subprocess.Popen(cmd_lint, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=dirnm, shell=False, startupinfo=startupinfo)
            else:
                p = subprocess.Popen(cmd_lint, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=dirnm, shell=False)
        else:
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                p = subprocess.Popen(cmd_lint, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, startupinfo=startupinfo)
            else:
                p = subprocess.Popen(cmd_lint, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
            p.stdin.write(src.encode('utf-8'))

        lint_out, lint_err = p.communicate()
        lintret = p.returncode

    if(lintret==0):
        cmd_fmt = [php_bin]

        if not debug:
            cmd_fmt.append("-ddisplay_errors=stderr")

        if psr1:
            cmd_fmt.append("-dshort_open_tag=On")

        cmd_fmt.append(formatter_path)
        cmd_fmt.append("--config="+config_file)

        if psr1:
            cmd_fmt.append("--psr1")

        if psr1_naming:
            cmd_fmt.append("--psr1-naming")

        if psr2:
            cmd_fmt.append("--psr2")

        if indent_with_space is True:
            cmd_fmt.append("--indent_with_space")
        elif indent_with_space > 0:
            cmd_fmt.append("--indent_with_space="+str(indent_with_space))

        if enable_auto_align:
            cmd_fmt.append("--enable_auto_align")

        if visibility_order:
            cmd_fmt.append("--visibility_order")

        if smart_linebreak_after_curly:
            cmd_fmt.append("--smart_linebreak_after_curly")

        if yoda:
            cmd_fmt.append("--yoda")

        if sgter is not None:
            cmd_fmt.append("--setters_and_getters="+sgter)
            cmd_fmt.append("--constructor="+sgter)

        if autoimport is True and oracleFname is not None:
            cmd_fmt.append("--oracleDB="+oracleFname)

        if len(passes) > 0:
            cmd_fmt.append("--passes="+','.join(passes))

        if len(excludes) > 0:
            cmd_fmt.append("--exclude="+','.join(excludes))

        if debug:
            cmd_fmt.append("-v")

        if sgter is None:
            cmd_fmt.append("-o=-")

        if src is None:
            cmd_fmt.append(uri)
        else:
            cmd_fmt.append("-")

        print_debug("cmd_fmt: ", cmd_fmt)

        if src is None:
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                p = subprocess.Popen(cmd_fmt, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=dirnm, shell=False, startupinfo=startupinfo)
            else:
                p = subprocess.Popen(cmd_fmt, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=dirnm, shell=False)
        else:
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                p = subprocess.Popen(cmd_fmt, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, startupinfo=startupinfo)
            else:
                p = subprocess.Popen(cmd_fmt, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

        if src is not None:
            p.stdin.write(src.encode('utf-8'))

        res, err = p.communicate()

        print_debug("p:\n", p.returncode)
        print_debug("err:\n", err.decode('utf-8'))

        if p.returncode != 0:
            return ''

        if sgter is not None:
            sublime.set_timeout(revert_active_window, 50)

        return res.decode('utf-8')
    else:
        sublime.status_message("phpfmt: format failed - syntax errors found")
        print_debug("lint error: ", lint_out)


def dogeneratephpdoc(eself, eview):
    self = eself
    view = eview
    s = sublime.load_settings('phpfmt.sublime-settings')

    additional_extensions = s.get("additional_extensions", [])
    autoimport = s.get("autoimport", True)
    debug = s.get("debug", False)
    enable_auto_align = s.get("enable_auto_align", False)
    ignore_list = s.get("ignore_list", "")
    indent_with_space = s.get("indent_with_space", False)
    psr1 = s.get("psr1", False)
    psr1_naming = s.get("psr1_naming", psr1)
    psr2 = s.get("psr2", False)
    smart_linebreak_after_curly = s.get("smart_linebreak_after_curly", True)
    visibility_order = s.get("visibility_order", False)
    yoda = s.get("yoda", False)

    passes = s.get("passes", [])

    php_bin = s.get("php_bin", "php")
    formatter_path = os.path.join(dirname(realpath(sublime.packages_path())), "Packages", "phpfmt", "fmt.phar")

    config_file = os.path.join(dirname(realpath(sublime.packages_path())), "Packages", "phpfmt", "php.tools.ini")

    uri = view.file_name()
    dirnm, sfn = os.path.split(uri)
    ext = os.path.splitext(uri)[1][1:]

    if "php" != ext and not ext in additional_extensions:
        print_debug("phpfmt: not a PHP file")
        sublime.status_message("phpfmt: not a PHP file")
        return False

    if not os.path.isfile(php_bin) and not php_bin == "php":
        print_debug("Can't find PHP binary file at "+php_bin)
        sublime.error_message("Can't find PHP binary file at "+php_bin)

    print_debug("phpfmt:", uri)
    if enable_auto_align:
        print_debug("auto align: enabled")
    else:
        print_debug("auto align: disabled")



    cmd_lint = [php_bin,"-l",uri];
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        p = subprocess.Popen(cmd_lint, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=dirnm, shell=False, startupinfo=startupinfo)
    else:
        p = subprocess.Popen(cmd_lint, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=dirnm, shell=False)
    lint_out, lint_err = p.communicate()

    if(p.returncode==0):
        cmd_fmt = [php_bin]

        if not debug:
            cmd_fmt.append("-ddisplay_errors=stderr")

        cmd_fmt.append(formatter_path)
        cmd_fmt.append("--config="+config_file)

        if psr1:
            cmd_fmt.append("--psr1")

        if psr1_naming:
            cmd_fmt.append("--psr1-naming")

        if psr2:
            cmd_fmt.append("--psr2")

        if indent_with_space:
            cmd_fmt.append("--indent_with_space")
        elif indent_with_space > 0:
            cmd_fmt.append("--indent_with_space="+str(indent_with_space))

        if enable_auto_align:
            cmd_fmt.append("--enable_auto_align")

        if visibility_order:
            cmd_fmt.append("--visibility_order")

        passes.append("GeneratePHPDoc")
        if len(passes) > 0:
            cmd_fmt.append("--passes="+','.join(passes))

        cmd_fmt.append(uri)

        uri_tmp = uri + "~"

        print_debug("cmd_fmt: ", cmd_fmt)

        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            p = subprocess.Popen(cmd_fmt, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=dirnm, shell=False, startupinfo=startupinfo)
        else:
            p = subprocess.Popen(cmd_fmt, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=dirnm, shell=False)
        res, err = p.communicate()
        print_debug("err:\n", err.decode('utf-8'))
        sublime.set_timeout(revert_active_window, 50)
    else:
        print_debug("lint error: ", lint_out)

def doreordermethod(eself, eview):
    self = eself
    view = eview
    s = sublime.load_settings('phpfmt.sublime-settings')

    additional_extensions = s.get("additional_extensions", [])
    autoimport = s.get("autoimport", True)
    debug = s.get("debug", False)
    enable_auto_align = s.get("enable_auto_align", False)
    ignore_list = s.get("ignore_list", "")
    indent_with_space = s.get("indent_with_space", False)
    psr1 = s.get("psr1", False)
    psr1_naming = s.get("psr1_naming", psr1)
    psr2 = s.get("psr2", False)
    smart_linebreak_after_curly = s.get("smart_linebreak_after_curly", True)
    visibility_order = s.get("visibility_order", False)
    yoda = s.get("yoda", False)

    passes = s.get("passes", [])

    php_bin = s.get("php_bin", "php")
    formatter_path = os.path.join(dirname(realpath(sublime.packages_path())), "Packages", "phpfmt", "fmt.phar")

    config_file = os.path.join(dirname(realpath(sublime.packages_path())), "Packages", "phpfmt", "php.tools.ini")

    uri = view.file_name()
    dirnm, sfn = os.path.split(uri)
    ext = os.path.splitext(uri)[1][1:]

    if "php" != ext and not ext in additional_extensions:
        print_debug("phpfmt: not a PHP file")
        sublime.status_message("phpfmt: not a PHP file")
        return False

    if not os.path.isfile(php_bin) and not php_bin == "php":
        print_debug("Can't find PHP binary file at "+php_bin)
        sublime.error_message("Can't find PHP binary file at "+php_bin)


    print_debug("phpfmt:", uri)
    if enable_auto_align:
        print_debug("auto align: enabled")
    else:
        print_debug("auto align: disabled")



    cmd_lint = [php_bin,"-l",uri];
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        p = subprocess.Popen(cmd_lint, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=dirnm, shell=False, startupinfo=startupinfo)
    else:
        p = subprocess.Popen(cmd_lint, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=dirnm, shell=False)
    lint_out, lint_err = p.communicate()

    if(p.returncode==0):
        cmd_fmt = [php_bin]

        if not debug:
            cmd_fmt.append("-ddisplay_errors=stderr")

        cmd_fmt.append(formatter_path)
        cmd_fmt.append("--config="+config_file)

        if psr1:
            cmd_fmt.append("--psr1")

        if psr1_naming:
            cmd_fmt.append("--psr1-naming")

        if psr2:
            cmd_fmt.append("--psr2")

        if indent_with_space:
            cmd_fmt.append("--indent_with_space")
        elif indent_with_space > 0:
            cmd_fmt.append("--indent_with_space="+str(indent_with_space))

        if enable_auto_align:
            cmd_fmt.append("--enable_auto_align")

        if visibility_order:
            cmd_fmt.append("--visibility_order")

        passes.append("OrganizeClass")
        if len(passes) > 0:
            cmd_fmt.append("--passes="+','.join(passes))

        cmd_fmt.append(uri)

        uri_tmp = uri + "~"

        print_debug("cmd_fmt: ", cmd_fmt)

        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            p = subprocess.Popen(cmd_fmt, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=dirnm, shell=False, startupinfo=startupinfo)
        else:
            p = subprocess.Popen(cmd_fmt, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=dirnm, shell=False)
        res, err = p.communicate()
        print_debug("err:\n", err.decode('utf-8'))
        sublime.set_timeout(revert_active_window, 50)
    else:
        print_debug("lint error: ", lint_out)

def debugEnvironment(php_bin, formatter_path):
    ret = ""
    cmd_ver = [php_bin,"-v"];
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        p = subprocess.Popen(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, startupinfo=startupinfo)
    else:
        p = subprocess.Popen(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    res, err = p.communicate()
    ret += ("phpfmt (php version):\n"+res.decode('utf-8'))
    if err.decode('utf-8'):
        ret += ("phpfmt (php version) err:\n"+err.decode('utf-8'))
    ret += "\n"

    cmd_ver = [php_bin,"-m"];
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        p = subprocess.Popen(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, startupinfo=startupinfo)
    else:
        p = subprocess.Popen(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    res, err = p.communicate()
    if res.decode('utf-8').find("tokenizer") != -1:
        ret += ("phpfmt (php tokenizer) found\n")
    else:
        ret += ("phpfmt (php tokenizer):\n"+res.decode('utf-8'))
        if err.decode('utf-8'):
            ret += ("phpfmt (php tokenizer) err:\n"+err.decode('utf-8'))
    ret += "\n"

    cmd_ver = [php_bin,formatter_path,"--version"];
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        p = subprocess.Popen(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, startupinfo=startupinfo)
    else:
        p = subprocess.Popen(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    res, err = p.communicate()
    ret += ("phpfmt (fmt.phar version):\n"+res.decode('utf-8'))
    if err.decode('utf-8'):
        ret += ("phpfmt (fmt.phar version) err:\n"+err.decode('utf-8'))
    ret += "\n"

    return ret

def revert_active_window():
    sublime.active_window().active_view().run_command("revert")
    sublime.active_window().active_view().run_command("phpcs_sniff_this_file")

def lookForOracleFile(view):
        uri = view.file_name()
        oracleDirNm, sfn = os.path.split(uri)
        originalDirNm = oracleDirNm

        while oracleDirNm != "/":
            oracleFname = oracleDirNm+os.path.sep+"oracle.sqlite"
            if os.path.isfile(oracleFname):
                return True
            origOracleDirNm = oracleDirNm
            oracleDirNm = os.path.dirname(oracleDirNm)
            if origOracleDirNm == oracleDirNm:
                return False
        return False

def outputToPanel(name, eself, eedit, message):
        eself.output_view = eself.view.window().get_output_panel(name)
        eself.view.window().run_command("show_panel", {"panel": "output."+name})
        eself.output_view.set_read_only(False)
        eself.output_view.insert(eedit, eself.output_view.size(), message)
        eself.output_view.set_read_only(True)

def hidePanel(name, eself, eedit):
        eself.output_view = eself.view.window().get_output_panel(name)
        eself.view.window().run_command("hide_panel", {"panel": "output."+name})

class phpfmt(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        s = sublime.load_settings('phpfmt.sublime-settings')
        format_on_save = s.get("format_on_save", True)

        if format_on_save:
            view.run_command('php_fmt')

class AnalyseThisCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if not lookForOracleFile(self.view):
            sublime.active_window().active_view().run_command("build_oracle")
            return False

        lookTerm = (self.view.substr(self.view.word(self.view.sel()[0].a)))

        s = sublime.load_settings('phpfmt.sublime-settings')
        php_bin = s.get("php_bin", "php")
        oraclePath = os.path.join(dirname(realpath(sublime.packages_path())), "Packages", "phpfmt", "oracle.php")

        uri = self.view.file_name()
        dirNm, sfn = os.path.split(uri)
        ext = os.path.splitext(uri)[1][1:]

        oracleDirNm = dirNm
        while oracleDirNm != "/":
            oracleFname = oracleDirNm+os.path.sep+"oracle.sqlite"
            if os.path.isfile(oracleFname):
                break
            origOracleDirNm = oracleDirNm
            oracleDirNm = os.path.dirname(oracleDirNm)
            if origOracleDirNm == oracleDirNm:
                break

        cmdOracle = [php_bin]
        cmdOracle.append(oraclePath)
        cmdOracle.append("introspect")
        cmdOracle.append(lookTerm)
        print_debug(cmdOracle+'asdasd')
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            p = subprocess.Popen(cmdOracle, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=oracleDirNm, shell=False, startupinfo=startupinfo)
        else:
            p = subprocess.Popen(cmdOracle, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=oracleDirNm, shell=False)
        res, err = p.communicate()

        print_debug("phpfmt (introspect): "+res.decode('utf-8'))
        print_debug("phpfmt (introspect) err: "+err.decode('utf-8'))

        outputToPanel("phpfmtintrospect", self, edit, "Analysis:\n"+res.decode('utf-8'));


lastCalltip = ""
class CalltipCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global lastCalltip
        uri = self.view.file_name()
        dirnm, sfn = os.path.split(uri)
        ext = os.path.splitext(uri)[1][1:]

        s = sublime.load_settings('phpfmt.sublime-settings')

        additional_extensions = s.get("additional_extensions", [])
        if "php" != ext and not ext in additional_extensions:
            return False

        if not lookForOracleFile(self.view):
            return False

        lookTerm = (self.view.substr(self.view.word(self.view.sel()[0].a)))
        if lastCalltip == lookTerm:
            return False

        lastCalltip = lookTerm

        php_bin = s.get("php_bin", "php")
        oraclePath = os.path.join(dirname(realpath(sublime.packages_path())), "Packages", "phpfmt", "oracle.php")

        uri = self.view.file_name()
        dirNm, sfn = os.path.split(uri)
        ext = os.path.splitext(uri)[1][1:]

        oracleDirNm = dirNm
        while oracleDirNm != "/":
            oracleFname = oracleDirNm+os.path.sep+"oracle.sqlite"
            if os.path.isfile(oracleFname):
                break
            origOracleDirNm = oracleDirNm
            oracleDirNm = os.path.dirname(oracleDirNm)
            if origOracleDirNm == oracleDirNm:
                break

        cmdOracle = [php_bin]
        cmdOracle.append(oraclePath)
        cmdOracle.append("calltip")
        cmdOracle.append(lookTerm)
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            p = subprocess.Popen(cmdOracle, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=oracleDirNm, shell=False, startupinfo=startupinfo)
        else:
            p = subprocess.Popen(cmdOracle, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=oracleDirNm, shell=False)
        res, err = p.communicate()

        output = res.decode('utf-8');

        self.view.set_status("phpfmt", output)

class DebugEnvCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        s = sublime.load_settings('phpfmt.sublime-settings')

        php_bin = s.get("php_bin", "php")
        formatter_path = os.path.join(dirname(realpath(sublime.packages_path())), "Packages", "phpfmt", "fmt.phar")

        s = debugEnvironment(php_bin, formatter_path)
        sublime.message_dialog(s)

class FmtNowCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        vsize = self.view.size()
        src = self.view.substr(sublime.Region(0, vsize))
        if not src.strip():
            return

        src = dofmt(self, self.view, None, src, True)
        if src is False or src == "":
            return False

        _, err = merge(self.view, vsize, src, edit)
        print_debug(err)

class TogglePassMenuCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        s = sublime.load_settings('phpfmt.sublime-settings')
        php_bin = s.get("php_bin", "php")
        formatter_path = os.path.join(dirname(realpath(sublime.packages_path())), "Packages", "phpfmt", "fmt.phar")

        cmd_passes = [php_bin,formatter_path,'--list-simple'];
        print_debug(cmd_passes)

        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            p = subprocess.Popen(cmd_passes, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, startupinfo=startupinfo)
        else:
            p = subprocess.Popen(cmd_passes, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

        out, err = p.communicate()

        descriptions = out.decode("utf-8").strip().split(os.linesep)

        def on_done(i):
            if i >= 0 :
                s = sublime.load_settings('phpfmt.sublime-settings')
                passes = s.get('passes', [])
                chosenPass = descriptions[i].split(' ')
                option = chosenPass[0]

                passDesc = option

                if option in passes:
                    passes.remove(option)
                    msg = "phpfmt: "+passDesc+" disabled"
                    print_debug(msg)
                    sublime.status_message(msg)
                else:
                    passes.append(option)
                    msg = "phpfmt: "+passDesc+" enabled"
                    print_debug(msg)
                    sublime.status_message(msg)

                s.set('passes', passes)
                sublime.save_settings('phpfmt.sublime-settings')

        self.view.window().show_quick_panel(descriptions, on_done, sublime.MONOSPACE_FONT)

class ToggleExcludeMenuCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        s = sublime.load_settings('phpfmt.sublime-settings')
        php_bin = s.get("php_bin", "php")
        formatter_path = os.path.join(dirname(realpath(sublime.packages_path())), "Packages", "phpfmt", "fmt.phar")

        cmd_passes = [php_bin,formatter_path,'--list-simple'];
        print_debug(cmd_passes)

        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            p = subprocess.Popen(cmd_passes, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, startupinfo=startupinfo)
        else:
            p = subprocess.Popen(cmd_passes, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

        out, err = p.communicate()

        descriptions = out.decode("utf-8").strip().split(os.linesep)

        def on_done(i):
            if i >= 0 :
                s = sublime.load_settings('phpfmt.sublime-settings')
                excludes = s.get('excludes', [])
                chosenPass = descriptions[i].split(' ')
                option = chosenPass[0]

                passDesc = option

                if option in excludes:
                    excludes.remove(option)
                    msg = "phpfmt: "+passDesc+" disabled"
                    print_debug(msg)
                    sublime.status_message(msg)
                else:
                    excludes.append(option)
                    msg = "phpfmt: "+passDesc+" enabled"
                    print_debug(msg)
                    sublime.status_message(msg)

                s.set('excludes', excludes)
                sublime.save_settings('phpfmt.sublime-settings')

        self.view.window().show_quick_panel(descriptions, on_done, sublime.MONOSPACE_FONT)

class ToggleCommand(sublime_plugin.TextCommand):
    def run(self, edit, option):
        s = sublime.load_settings('phpfmt.sublime-settings')
        options = {
            "autocomplete":"autocomplete",
            "autoimport":"dependency autoimport",
            "enable_auto_align":"auto align",
            "format_on_save":"format on save",
            "psr1":"PSR1",
            "psr1_naming":"PSR1 Class and Method Naming",
            "psr2":"PSR2",
            "readini":"look for .php.tools.ini",
            "smart_linebreak_after_curly":"smart linebreak after curly",
            "skip_if_ini_missing":"skip if ini file is missing",
            "visibility_order":"visibility order",
            "yoda":"yoda mode",
        }
        s = sublime.load_settings('phpfmt.sublime-settings')
        value = s.get(option, False)

        if value:
            s.set(option, False)
            msg = "phpfmt: "+options[option]+" disabled"
            print_debug(msg)
            sublime.status_message(msg)
        else:
            s.set(option, True)
            msg = "phpfmt: "+options[option]+" enabled"
            print_debug(msg)
            sublime.status_message(msg)

        sublime.save_settings('phpfmt.sublime-settings')

class UpdatePhpBinCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        def execute(text):
            s = sublime.load_settings('phpfmt.sublime-settings')
            s.set("php_bin", text)

        s = sublime.load_settings('phpfmt.sublime-settings')
        self.view.window().show_input_panel('php binary path:', s.get("php_bin", ""), execute, None, None)

class OrderMethodCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        doreordermethod(self, self.view)

class GeneratePhpdocCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        dogeneratephpdoc(self, self.view)

class SgterSnakeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        dofmt(self, self.view, 'snake')

class SgterCamelCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        dofmt(self, self.view, 'camel')

class SgterGoCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        dofmt(self, self.view, 'golang')

class BuildOracleCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        def buildDB():
            if self.msgFile is not None:
                self.msgFile.window().run_command('close_file')
            s = sublime.load_settings('phpfmt.sublime-settings')
            php_bin = s.get("php_bin", "php")
            oraclePath = os.path.join(dirname(realpath(sublime.packages_path())), "Packages", "phpfmt", "oracle.php")
            cmdOracle = [php_bin]
            cmdOracle.append(oraclePath)
            cmdOracle.append("flush")
            cmdOracle.append(self.dirNm)
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                p = subprocess.Popen(cmdOracle, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.dirNm, shell=False, startupinfo=startupinfo)
            else:
                p = subprocess.Popen(cmdOracle, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.dirNm, shell=False)
            res, err = p.communicate()
            print_debug("phpfmt (oracle): "+res.decode('utf-8'))
            print_debug("phpfmt (oracle) err: "+err.decode('utf-8'))
            sublime.status_message("phpfmt (oracle): done")


        #sublime.set_timeout_async(self.long_command, 0)
        def askForDirectory(text):
            self.dirNm = text
            sublime.set_timeout_async(buildDB, 0)

        view = self.view
        s = sublime.load_settings('phpfmt.sublime-settings')
        php_bin = s.get("php_bin", "php")

        uri = view.file_name()
        oracleDirNm, sfn = os.path.split(uri)
        originalDirNm = oracleDirNm

        while oracleDirNm != "/":
            oracleFname = oracleDirNm+os.path.sep+"oracle.sqlite"
            if os.path.isfile(oracleFname):
                break
            origOracleDirNm = oracleDirNm
            oracleDirNm = os.path.dirname(oracleDirNm)
            if origOracleDirNm == oracleDirNm:
                break

        self.msgFile = None
        if not os.path.isfile(oracleFname):
            print_debug("phpfmt (oracle file): not found -- dialog")
            self.msgFile = self.view.window().open_file(os.path.join(dirname(realpath(sublime.packages_path())), "Packages", "phpfmt", "message"))
            self.msgFile.set_read_only(True)
            self.view.window().show_input_panel('location:', originalDirNm, askForDirectory, None, None)
        else:
            print_debug("phpfmt (oracle file): "+oracleFname)
            print_debug("phpfmt (oracle dir): "+oracleDirNm)
            self.dirNm = oracleDirNm
            sublime.set_timeout_async(buildDB, 0)

class IndentWithSpacesCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        def setIndentWithSpace(text):
            s = sublime.load_settings('phpfmt.sublime-settings')
            v = text.strip()
            if not v:
                v = False
            else:
                v = int(v)
            s.set("indent_with_space", v)
            sublime.save_settings('phpfmt.sublime-settings')
            sublime.status_message("phpfmt (indentation): done")
            sublime.active_window().active_view().run_command("fmt_now")

        s = sublime.load_settings('phpfmt.sublime-settings')
        spaces = s.get("indent_with_space", 4)
        if not spaces:
            spaces = ""
        spaces = str(spaces)
        self.view.window().show_input_panel('how many spaces? (leave it empty to return to tabs)', spaces, setIndentWithSpace, None, None)

class PHPFmtComplete(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        s = sublime.load_settings('phpfmt.sublime-settings')

        autocomplete = s.get("autocomplete", False)
        if autocomplete is False:
                return []

        pos = locations[0]
        scopes = view.scope_name(pos).split()
        if not ('source.php.embedded.block.html' in scopes or 'source.php' in scopes):
            return []


        print_debug("phpfmt (autocomplete): "+prefix);

        comps = []

        uri = view.file_name()
        dirNm, sfn = os.path.split(uri)
        ext = os.path.splitext(uri)[1][1:]


        oracleDirNm = dirNm
        while oracleDirNm != "/":
            oracleFname = oracleDirNm+os.path.sep+"oracle.sqlite"
            if os.path.isfile(oracleFname):
                break
            origOracleDirNm = oracleDirNm
            oracleDirNm = os.path.dirname(oracleDirNm)
            if origOracleDirNm == oracleDirNm:
                break


        if not os.path.isfile(oracleFname):
            sublime.status_message("phpfmt: autocomplete database not found")
            return []

        if prefix in "namespace":
            ns = dirNm.replace(oracleDirNm, '').replace('/','\\')
            if ns.startswith('\\'):
                ns = ns[1:]
            comps.append((
                '%s \t %s \t %s' % ("namespace", ns, "namespace"),
                '%s %s;\n${0}' % ("namespace", ns),
            ))

        if prefix in "class":
            print_debug("class guess")
            className = sfn.split(".")[0]
            comps.append((
                '%s \t %s \t %s' % ("class", className, "class"),
                '%s %s {\n\t${0}\n}\n' % ("class", className),
            ))

        php_bin = s.get("php_bin", "php")
        oraclePath = os.path.join(dirname(realpath(sublime.packages_path())), "Packages", "phpfmt", "oracle.php")
        cmdOracle = [php_bin]
        cmdOracle.append(oraclePath)
        cmdOracle.append("autocomplete")
        cmdOracle.append(prefix)
        print_debug(cmdOracle)
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            p = subprocess.Popen(cmdOracle, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=oracleDirNm, shell=False, startupinfo=startupinfo)
        else:
            p = subprocess.Popen(cmdOracle, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=oracleDirNm, shell=False)
        res, err = p.communicate()
        print_debug("phpfmt (autocomplete) err: "+err.decode('utf-8'))

        f = res.decode('utf-8').split('\n')
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            if len(row) > 0:
                if "class" == row[3]:
                    comps.append((
                        '%s \t %s \t %s' % (row[1], row[0], "class"),
                        '%s(${0})' % (row[1]),
                    ))
                    comps.append((
                        '%s \t %s \t %s' % (row[0], row[0], "class"),
                        '%s(${0})' % (row[0]),
                    ))
                if "method" == row[3]:
                    comps.append((
                        '%s \t %s \t %s' % (row[1], row[2], "method"),
                        '%s' % (row[0].replace('$','\$')),
                    ))

        return comps

s = sublime.load_settings('phpfmt.sublime-settings')
version = s.get('version', 1)
s.set('version', version)
sublime.save_settings('phpfmt.sublime-settings')

if version == 2:
    # Convert to version 3
    print_debug("Convert to version 3")
    s.set('version', 3)
    sublime.save_settings('phpfmt.sublime-settings')

if version == 3:
    # Convert to version 3
    print_debug("Convert to version 4")
    s.set('version', 4)
    passes = s.get('passes', [])
    passes.append("ReindentSwitchBlocks")
    s.set('passes', passes)
    sublime.save_settings('phpfmt.sublime-settings')


# def selfupdate():
#     s = sublime.load_settings('phpfmt.sublime-settings')
#     php_bin = s.get("php_bin", "php")
#     formatter_path = os.path.join(dirname(realpath(sublime.packages_path())), "Packages", "phpfmt", "fmt.phar")

#     print_debug("Selfupdate")
#     cmd_update = [php_bin, formatter_path, '--selfupdate']
#     if os.name == 'nt':
#         startupinfo = subprocess.STARTUPINFO()
#         startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
#         p = subprocess.Popen(cmd_update, shell=False, startupinfo=startupinfo)
#     else:
#         p = subprocess.Popen(cmd_update, shell=False)

# sublime.set_timeout(selfupdate, 3000)


def _ct_poller():
    s = sublime.load_settings('phpfmt.sublime-settings')
    if s.get("calltip", False):
        try:
            view = sublime.active_window().active_view()
            view.run_command('calltip')
        except Exception:
            pass
        sublime.set_timeout(_ct_poller, 5000)

_ct_poller()


class PhpFmtCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        vsize = self.view.size()
        src = self.view.substr(sublime.Region(0, vsize))
        if not src.strip():
            return

        src = dofmt(self, self.view, None, src)
        if src is False or src == "":
            return False

        _, err = merge(self.view, vsize, src, edit)
        print_debug(err)

class MergeException(Exception):
    pass

def _merge(view, size, text, edit):
    def ss(start, end):
        return view.substr(sublime.Region(start, end))
    dmp = diff_match_patch()
    diffs = dmp.diff_main(ss(0, size), text, False)
    dmp.diff_cleanupEfficiency(diffs)
    i = 0
    dirty = False
    for d in diffs:
        k, s = d
        l = len(s)
        if k == 0:
            # match
            l = len(s)
            if ss(i, i+l) != s:
                raise MergeException('mismatch', dirty)
            i += l
        else:
            dirty = True
            if k > 0:
                # insert
                view.insert(edit, i, s)
                i += l
            else:
                # delete
                if ss(i, i+l) != s:
                    raise MergeException('mismatch', dirty)
                view.erase(edit, sublime.Region(i, i+l))
    return dirty

def merge(view, size, text, edit):
    vs = view.settings()
    ttts = vs.get("translate_tabs_to_spaces")
    vs.set("translate_tabs_to_spaces", False)
    origin_src = view.substr(sublime.Region(0, view.size()))
    if not origin_src.strip():
        vs.set("translate_tabs_to_spaces", ttts)
        return (False, '')

    try:
        dirty = False
        err = ''
        if size < 0:
            size = view.size()
        dirty = _merge(view, size, text, edit)
    except MergeException as ex:
        dirty = True
        err = "Could not merge changes into the buffer, edit aborted: %s" % ex[0]
        view.replace(edit, sublime.Region(0, view.size()), origin_src)
    except Exception as ex:
        err = "error: %s" % ex
    finally:
        vs.set("translate_tabs_to_spaces", ttts)
        return (dirty, err)
