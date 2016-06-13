# [phpfmt](https://github.com/phpfmt/fmt) support for Sublime Text 2/3

## Installation

#### Requirements
- **You must have a running copy of PHP on the machine you are running Sublime Text**

Plugin runs with PHP 7.0 or newer installed in the machine running the plugin.

#### Install this plugin through Package Manager.

- In Sublime Text press `ctrl+shift+P`
- Choose `Package Control: Install Package`
- Choose `phpfmt`

#### Configuration (Windows)

- Edit configuration file (`%AppData%\Sublime Text\Packages\phpfmt\phpfmt.sublime-settings`)
- For field `"php_bin"` enter the path to the php.exe
  Example: `"php_bin":"c:/PHP/php.exe"`

#### Configuration (OS X and Linux)

- Edit configuration file (`phpfmt.sublime-settings`)
- For field `"php_bin"` enter the path to the php
  Example: `"php_bin":"/usr/local/bin/php"`

### Settings

Prefer using the toggle options at command palette. However you might find yourself in need to setup where PHP is running, use this option below for the configuration file.
```
{
"php_bin":"/usr/local/bin/php",
}
```

**The following features are available through command palette (`ctrl+shift+P` or `cmd+shift+P`) :**

 *  phpfmt: format now
 *  phpfmt: indentation with spaces
 *  phpfmt: toggle additional transformations
 *  phpfmt: toggle excluded transformations
 *  phpfmt: toggle skip execution when .php.tools.ini is missing
 *  phpfmt: toggle autocomplete
 *  phpfmt: toggle dependency autoimport
 *  phpfmt: toggle format on save
 *  phpfmt: toggle PSR1 - Class and Methods names
 *  phpfmt: toggle PSR1
 *  phpfmt: toggle PSR2
 *  phpfmt: analyse this
 *  phpfmt: build autocomplete database
 *  phpfmt: getter and setter (camelCase)
 *  phpfmt: getter and setter (Go)
 *  phpfmt: getter and setter (snake_case)
 *  phpfmt: generate PHPDoc block
 *  phpfmt: look for .php.tools.ini
 *  phpfmt: reorganize content of class
 *  phpfmt: enable/disable additional transformations
 *  phpfmt: troubleshoot information
 *  phpfmt: update PHP binary path


### Currently Supported Transformations:

 * AddMissingParentheses             Add extra parentheses in new instantiations.
 * AliasToMaster                     Replace function aliases to their masters - only basic syntax alias.
 * AlignConstVisibilityEquals        Vertically align "=" of visibility and const blocks.
 * AlignDoubleArrow                  Vertically align T_DOUBLE_ARROW (=>).
 * AlignDoubleSlashComments          Vertically align "//" comments.
 * AlignEquals                       Vertically align "=".
 * AlignGroupDoubleArrow             Vertically align T_DOUBLE_ARROW (=>) by line groups.
 * AlignPHPCode                      Align PHP code within HTML block.
 * AlignTypehint                     Vertically align function type hints.
 * AllmanStyleBraces                 Transform all curly braces into Allman-style.
 * AutoPreincrement                  Automatically convert postincrement to preincrement.
 * AutoSemicolon                     Add semicolons in statements ends.
 * CakePHPStyle                      Applies CakePHP Coding Style
 * ClassToSelf                       "self" is preferred within class, trait or interface.
 * ClassToStatic                     "static" is preferred within class, trait or interface.
 * ConvertOpenTagWithEcho            Convert from "<?=" to "<?php echo ".
 * DocBlockToComment                 Replace docblocks with regular comments when used in non structural elements.
 * DoubleToSingleQuote               Convert from double to single quotes.
 * EchoToPrint                       Convert from T_ECHO to print.
 * EncapsulateNamespaces             Encapsulate namespaces with curly braces
 * GeneratePHPDoc                    Automatically generates PHPDoc blocks
 * IndentTernaryConditions           Applies indentation to ternary conditions.
 * JoinToImplode                     Replace implode() alias (join() -> implode()).
 * LeftWordWrap                      Word wrap at 80 columns - left justify.
 * LongArray                         Convert short to long arrays.
 * MergeElseIf                       Merge if with else.
 * SplitElseIf                       Merge if with else.
 * MergeNamespaceWithOpenTag         Ensure there is no more than one linebreak before namespace
 * MildAutoPreincrement              Automatically convert postincrement to preincrement. (Deprecated pass. Use AutoPreincrement instead).
 * NewLineBeforeReturn               Add an empty line before T_RETURN.
 * OrganizeClass                     Organize class, interface and trait structure.
 * OrderAndRemoveUseClauses          Order use block and remove unused imports.
 * OnlyOrderUseClauses               Order use block - do not remove unused imports.
 * OrderMethod                       Organize class, interface and trait structure.
 * OrderMethodAndVisibility          Organize class, interface and trait structure.
 * PHPDocTypesToFunctionTypehint     Read variable types from PHPDoc blocks and add them in function signatures.
 * PrettyPrintDocBlocks              Prettify Doc Blocks
 * PSR2EmptyFunction                 Merges in the same line of function header the body of empty functions.
 * PSR2MultilineFunctionParams       Break function parameters into multiple lines.
 * ReindentAndAlignObjOps            Align object operators.
 * ReindentSwitchBlocks              Reindent one level deeper the content of switch blocks.
 * RemoveIncludeParentheses          Remove parentheses from include declarations.
 * RemoveSemicolonAfterCurly         Remove semicolon after closing curly brace.
 * RemoveUseLeadingSlash             Remove leading slash in T_USE imports.
 * ReplaceBooleanAndOr               Convert from "and"/"or" to "&&"/"||". Danger! This pass leads to behavior change.
 * ReplaceIsNull                     Replace is_null($a) with null === $a.
 * RestoreComments                   Revert any formatting of comments content.
 * ReturnNull                        Simplify empty returns.
 * ShortArray                        Convert old array into new array. (array() -> [])
 * SmartLnAfterCurlyOpen             Add line break when implicit curly block is added.
 * SortUseNameSpace                  Organize use clauses by length and alphabetic order.
 * SpaceAroundControlStructures      Add space around control structures.
 * SpaceAroundExclamationMark        Add spaces around exclamation mark.
 * SpaceBetweenMethods               Put space between methods.
 * StrictBehavior                    Activate strict option in array_search, base64_decode, in_array, array_keys, mb_detect_encoding. Danger! This pass leads to behavior change.
 * StrictComparison                  All comparisons are converted to strict. Danger! This pass leads to behavior change.
 * StripExtraCommaInArray            Remove trailing commas within array blocks
 * StripNewlineAfterClassOpen        Strip empty lines after class opening curly brace.
 * StripNewlineAfterCurlyOpen        Strip empty lines after opening curly brace.
 * StripNewlineWithinClassBody       Strip empty lines after class opening curly brace.
 * StripSpaces                       Remove all empty spaces
 * StripSpaceWithinControlStructures Strip empty lines within control structures.
 * TightConcat                       Ensure string concatenation does not have spaces, except when close to numbers.
 * TrimSpaceBeforeSemicolon          Remove empty lines before semi-colon.
 * UpgradeToPreg                     Upgrade ereg_* calls to preg_*
 * WordWrap                          Word wrap at 80 columns.
 * WrongConstructorName              Update old constructor names into new ones. http://php.net/manual/en/language.oop5.decon.php
 * YodaComparisons                   Execute Yoda Comparisons.

### What does it do?

<table>
<tr>
<td>Before</td>
<td>After</td>
</tr>
<tr>
<td>
<pre><code>&lt;?php
for($i = 0; $i &lt; 10; $i++)
{
if($i%2==0)
echo "Flipflop";
}
</code></pre>
</td>
<td>
<pre><code>&lt;?php
for ($i = 0; $i &lt; 10; $i++) {
  if ($i%2 == 0) {
    echo "Flipflop";
  }
}
</code></pre>
</td>
</tr>
<tr>
<td>
<pre><code>&lt;?php
$a = 10;
$otherVar = 20;
$third = 30;
</code></pre>
</td>
<td>
<pre><code>&lt;?php
$a        = 10;
$otherVar = 20;
$third    = 30;
</code></pre>
<i>This can be enabled with the option "enable_auto_align"</i>
</td>
</tr>
<tr>
<td>
<pre><code>&lt;?php
namespace NS\Something;
use \OtherNS\C;
use \OtherNS\B;
use \OtherNS\A;
use \OtherNS\D;

$a = new A();
$b = new C();
$d = new D();
</code></pre>
</td>
<td>
<pre><code>&lt;?php
namespace NS\Something;

use \OtherNS\A;
use \OtherNS\C;
use \OtherNS\D;

$a = new A();
$b = new C();
$d = new D();
</code></pre>
<i>note how it sorts the use clauses, and removes unused ones</i>
</td>
</tr>
</table>

### What does it do? - PSR version

<table>
<tr>
<td>Before</td>
<td>After</td>
</tr>
<tr>
<td>
<pre><code>&lt;?php
for($i = 0; $i &lt; 10; $i++)
{
if($i%2==0)
echo "Flipflop";
}
</code></pre>
</td>
<td>
<pre><code>&lt;?php
for ($i = 0; $i &lt; 10; $i++) {
    if ($i%2 == 0) {
        echo "Flipflop";
    }
}
</code></pre>
<i>Note the identation of 4 spaces.</i>
</td>
</tr>
<tr>
<td>
<pre><code>&lt;?php
class A {
function a(){
return 10;
}
}
</code></pre>
</td>
<td>
<pre><code>&lt;?php
class A
{
    public function a()
    {
        return 10;
    }
}
</code></pre>
<i>Note the braces position, and the visibility adjustment in the method a().</i>
</td>
</tr>
<tr>
<td>
<pre><code>&lt;?php
namespace NS\Something;
use \OtherNS\C;
use \OtherNS\B;
use \OtherNS\A;
use \OtherNS\D;

$a = new A();
$b = new C();
$d = new D();
</code></pre>
</td>
<td>
<pre><code>&lt;?php
namespace NS\Something;

use \OtherNS\A;
use \OtherNS\C;
use \OtherNS\D;

$a = new A();
$b = new C();
$d = new D();
</code></pre>
<i>note how it sorts the use clauses, and removes unused ones</i>
</td>
</tr>
</table>

### Troubleshooting
- Be sure you can run PHP from the command line.
- If you need support, please open an issue at [fmt issues](https://github.com/phpfmt/fmt/issues)

### The Most FAQ

***I want to use sublime-phpfmt, but it needs PHP 5.6 or newer and on my production
server I have PHP 5.5 or older. What should I do?***

Consider installing a standalone PHP 5.6 in a separate directory and have it *not*
configured in the environment. Within the plugin, ensure `php_bin` parameter is pointed to this standalone installation.

### Acknowledgements
- GoSublime - for the method to update the formatted buffer
- Google's diff match patch - http://code.google.com/p/google-diff-match-patch/
