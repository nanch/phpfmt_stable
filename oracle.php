<?php
//Copyright (c) 2014, Carlos C
//All rights reserved.
//
//Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
//
//1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
//
//2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
//
//3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
//
//THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
define("ST_AT", "@");
define("ST_BRACKET_CLOSE", "]");
define("ST_BRACKET_OPEN", "[");
define("ST_COLON", ":");
define("ST_COMMA", ",");
define("ST_CONCAT", ".");
define("ST_CURLY_CLOSE", "}");
define("ST_CURLY_OPEN", "{");
define("ST_DIVIDE", "/");
define("ST_DOLLAR", "$");
define("ST_EQUAL", "=");
define("ST_EXCLAMATION", "!");
define("ST_IS_GREATER", ">");
define("ST_IS_SMALLER", "<");
define("ST_MINUS", "-");
define("ST_MODULUS", "%");
define("ST_PARENTHESES_CLOSE", ")");
define("ST_PARENTHESES_OPEN", "(");
define("ST_PLUS", "+");
define("ST_QUESTION", "?");
define("ST_QUOTE", '"');
define("ST_REFERENCE", "&");
define("ST_SEMI_COLON", ";");
define("ST_TIMES", "*");
define("ST_BITWISE_OR", "|");
define("ST_BITWISE_XOR", "^");
if (!defined("T_POW")) {
	define("T_POW", "**");
}
if (!defined("T_POW_EQUAL")) {
	define("T_POW_EQUAL", "**=");
}
if (!defined("T_YIELD")) {
	define("T_YIELD", "yield");
}
if (!defined("T_FINALLY")) {
	define("T_FINALLY", "finally");
}
;
abstract class FormatterPass {
	protected $indentChar = "\t";
	protected $newLine = "\n";
	protected $indent = 0;
	protected $code = '';
	protected $ptr = 0;
	protected $tkns = [];
	protected $useCache = false;
	protected $cache = [];
	protected $ignoreFutileTokens = [T_WHITESPACE, T_COMMENT, T_DOC_COMMENT];

	protected function appendCode($code = "") {
		$this->code .= $code;
	}

	private function calculateCacheKey($direction, $ignoreList, $token) {
		return $direction . "\x2" . implode('', $ignoreList) . "\x2" . (is_array($token) ? implode("\x2", $token) : $token);
	}

	abstract public function candidate($source, $foundTokens);
	abstract public function format($source);

	protected function getToken($token) {
		if (isset($token[1])) {
			return $token;
		} else {
			return [$token, $token];
		}
	}

	protected function getCrlf($true = true) {
		return $true ? $this->newLine : "";
	}

	protected function getCrlfIndent() {
		return $this->getCrlf() . $this->getIndent();
	}

	protected function getIndent($increment = 0) {
		return str_repeat($this->indentChar, $this->indent + $increment);
	}

	protected function getSpace($true = true) {
		return $true ? " " : "";
	}

	protected function hasLn($text) {
		return (false !== strpos($text, $this->newLine));
	}

	protected function hasLnAfter() {
		$id = null;
		$text = null;
		list($id, $text) = $this->inspectToken();
		return T_WHITESPACE === $id && $this->hasLn($text);
	}

	protected function hasLnBefore() {
		$id = null;
		$text = null;
		list($id, $text) = $this->inspectToken(-1);
		return T_WHITESPACE === $id && $this->hasLn($text);
	}

	protected function hasLnLeftToken() {
		list($id, $text) = $this->getToken($this->leftToken());
		return $this->hasLn($text);
	}

	protected function hasLnRightToken() {
		list($id, $text) = $this->getToken($this->rightToken());
		return $this->hasLn($text);
	}

	protected function inspectToken($delta = 1) {
		if (!isset($this->tkns[$this->ptr + $delta])) {
			return [null, null];
		}
		return $this->getToken($this->tkns[$this->ptr + $delta]);
	}

	protected function leftToken($ignoreList = [], $idx = false) {
		$i = $this->leftTokenIdx($ignoreList);

		return $this->tkns[$i];
	}

	protected function leftTokenIdx($ignoreList = []) {
		$ignoreList = $this->resolveIgnoreList($ignoreList);

		$i = $this->walkLeft($this->tkns, $this->ptr, $ignoreList);

		return $i;
	}

	protected function leftTokenIs($token, $ignoreList = []) {
		return $this->tokenIs('left', $token, $ignoreList);
	}

	protected function leftTokenSubsetIsAtIdx($tkns, $idx, $token, $ignoreList = []) {
		$ignoreList = $this->resolveIgnoreList($ignoreList);

		$idx = $this->walkLeft($tkns, $idx, $ignoreList);

		return $this->resolveTokenMatch($tkns, $idx, $token);
	}

	protected function leftUsefulToken() {
		return $this->leftToken($this->ignoreFutileTokens);
	}

	protected function leftUsefulTokenIdx() {
		return $this->leftTokenIdx($this->ignoreFutileTokens);
	}

	protected function leftUsefulTokenIs($token) {
		return $this->leftTokenIs($token, $this->ignoreFutileTokens);
	}

	protected function printAndStopAt($tknids) {
		if (is_scalar($tknids)) {
			$tknids = [$tknids];
		}
		$tknids = array_flip($tknids);
		while (list($index, $token) = each($this->tkns)) {
			list($id, $text) = $this->getToken($token);
			$this->ptr = $index;
			$this->cache = [];
			if (isset($tknids[$id])) {
				return [$id, $text];
			}
			$this->appendCode($text);
		}
	}

	protected function printBlock($start, $end) {
		$count = 1;
		while (list($index, $token) = each($this->tkns)) {
			list($id, $text) = $this->getToken($token);
			$this->ptr = $index;
			$this->cache = [];
			$this->appendCode($text);

			if ($start == $id) {
				++$count;
			}
			if ($end == $id) {
				--$count;
			}
			if (0 == $count) {
				break;
			}
		}
	}

	protected function printCurlyBlock() {
		$count = 1;
		while (list($index, $token) = each($this->tkns)) {
			list($id, $text) = $this->getToken($token);
			$this->ptr = $index;
			$this->cache = [];
			$this->appendCode($text);

			if (ST_CURLY_OPEN == $id) {
				++$count;
			}
			if (T_CURLY_OPEN == $id) {
				++$count;
			}
			if (T_DOLLAR_OPEN_CURLY_BRACES == $id) {
				++$count;
			}
			if (ST_CURLY_CLOSE == $id) {
				--$count;
			}
			if (0 == $count) {
				break;
			}
		}
	}

	protected function printUntil($tknid) {
		while (list($index, $token) = each($this->tkns)) {
			list($id, $text) = $this->getToken($token);
			$this->ptr = $index;
			$this->cache = [];
			$this->appendCode($text);
			if ($tknid == $id) {
				break;
			}
		}
	}

	protected function printUntilAny($tknids) {
		$tknids = array_flip($tknids);
		$whitespaceNewLine = false;
		if (isset($tknids[$this->newLine])) {
			$whitespaceNewLine = true;
		}
		while (list($index, $token) = each($this->tkns)) {
			list($id, $text) = $this->getToken($token);
			$this->ptr = $index;
			$this->cache = [];
			$this->appendCode($text);
			if ($whitespaceNewLine && T_WHITESPACE == $id && $this->hasLn($text)) {
				break;
			}
			if (isset($tknids[$id])) {
				break;
			}
		}
		return $id;
	}

	protected function printUntilTheEndOfString() {
		$this->printUntil(ST_QUOTE);
	}

	protected function render($tkns = null) {
		if (null == $tkns) {
			$tkns = $this->tkns;
		}

		$tkns = array_filter($tkns);
		$str = '';
		foreach ($tkns as $token) {
			list($id, $text) = $this->getToken($token);
			$str .= $text;
		}
		return $str;
	}

	protected function renderLight($tkns = null) {
		if (null == $tkns) {
			$tkns = $this->tkns;
		}
		$str = '';
		foreach ($tkns as $token) {
			$str .= $token[1];
		}
		return $str;
	}

	private function resolveIgnoreList($ignoreList = []) {
		if (empty($ignoreList)) {
			$ignoreList[T_WHITESPACE] = true;
		} else {
			$ignoreList = array_flip($ignoreList);
		}
		return $ignoreList;
	}

	private function resolveTokenMatch($tkns, $idx, $token) {
		if (!isset($tkns[$idx])) {
			return false;
		}

		$foundToken = $tkns[$idx];
		if ($foundToken === $token) {
			return true;
		} elseif (is_array($token) && isset($foundToken[1]) && in_array($foundToken[0], $token)) {
			return true;
		} elseif (is_array($token) && !isset($foundToken[1]) && in_array($foundToken, $token)) {
			return true;
		} elseif (isset($foundToken[1]) && $foundToken[0] == $token) {
			return true;
		}

		return false;
	}

	protected function rightToken($ignoreList = []) {
		$i = $this->rightTokenIdx($ignoreList);

		return $this->tkns[$i];
	}

	protected function rightTokenIdx($ignoreList = []) {
		$ignoreList = $this->resolveIgnoreList($ignoreList);

		$i = $this->walkRight($this->tkns, $this->ptr, $ignoreList);

		return $i;
	}

	protected function rightTokenIs($token, $ignoreList = []) {
		return $this->tokenIs('right', $token, $ignoreList);
	}

	protected function rightTokenSubsetIsAtIdx($tkns, $idx, $token, $ignoreList = []) {
		$ignoreList = $this->resolveIgnoreList($ignoreList);

		$idx = $this->walkRight($tkns, $idx, $ignoreList);

		return $this->resolveTokenMatch($tkns, $idx, $token);
	}

	protected function rightUsefulToken() {
		return $this->rightToken($this->ignoreFutileTokens);
	}

	// protected function rightUsefulTokenIdx($idx = false) {
	// 	return $this->rightTokenIdx($this->ignoreFutileTokens);
	// }

	protected function rightUsefulTokenIs($token) {
		return $this->rightTokenIs($token, $this->ignoreFutileTokens);
	}

	protected function rtrimAndAppendCode($code = "") {
		$this->code = rtrim($this->code) . $code;
	}

	protected function scanAndReplace(&$tkns, &$ptr, $start, $end, $call, $look_for) {
		$look_for = array_flip($look_for);
		$placeholder = '<?php' . ' /*\x2 PHPOPEN \x3*/';
		$tmp = '';
		$tknCount = 1;
		$foundPotentialTokens = false;
		while (list($ptr, $token) = each($tkns)) {
			list($id, $text) = $this->getToken($token);
			if (isset($look_for[$id])) {
				$foundPotentialTokens = true;
			}
			if ($start == $id) {
				++$tknCount;
			}
			if ($end == $id) {
				--$tknCount;
			}
			$tkns[$ptr] = null;
			if (0 == $tknCount) {
				break;
			}
			$tmp .= $text;
		}
		if ($foundPotentialTokens) {
			return $start . str_replace($placeholder, '', $this->{$call}($placeholder . $tmp)) . $end;
		}
		return $start . $tmp . $end;

	}

	protected function setIndent($increment) {
		$this->indent += $increment;
		if ($this->indent < 0) {
			$this->indent = 0;
		}
	}

	protected function siblings($tkns, $ptr) {
		$ignoreList = $this->resolveIgnoreList([T_WHITESPACE]);
		$left = $this->walkLeft($tkns, $ptr, $ignoreList);
		$right = $this->walkRight($tkns, $ptr, $ignoreList);
		return [$left, $right];
	}

	protected function substrCountTrailing($haystack, $needle) {
		return strlen(rtrim($haystack, " \t")) - strlen(rtrim($haystack, " \t" . $needle));
	}

	protected function tokenIs($direction, $token, $ignoreList = []) {
		if ('left' != $direction) {
			$direction = 'right';
		}
		if (!$this->useCache) {
			return $this->{$direction . 'tokenSubsetIsAtIdx'}($this->tkns, $this->ptr, $token, $ignoreList);
		}

		$key = $this->calculateCacheKey($direction, $ignoreList, $token);
		if (isset($this->cache[$key])) {
			return $this->cache[$key];
		}

		$ret = $this->{$direction . 'tokenSubsetIsAtIdx'}($this->tkns, $this->ptr, $token, $ignoreList);
		$this->cache[$key] = $ret;

		return $ret;
	}

	protected function walkAndAccumulateUntil(&$tkns, $tknid) {
		$ret = '';
		while (list($index, $token) = each($tkns)) {
			list($id, $text) = $this->getToken($token);
			$this->ptr = $index;
			$ret .= $text;
			if ($tknid == $id) {
				break;
			}
		}
		return $ret;
	}

	private function walkLeft($tkns, $idx, $ignoreList) {
		$i = $idx;
		while (--$i >= 0 && isset($tkns[$i][1]) && isset($ignoreList[$tkns[$i][0]]));
		return $i;
	}

	private function walkRight($tkns, $idx, $ignoreList) {
		$i = $idx;
		$tknsSize = sizeof($tkns) - 1;
		while (++$i < $tknsSize && isset($tkns[$i][1]) && isset($ignoreList[$tkns[$i][0]]));
		return $i;
	}

	protected function walkUntil($tknid) {
		while (list($index, $token) = each($this->tkns)) {
			list($id, $text) = $this->getToken($token);
			$this->ptr = $index;
			if ($id == $tknid) {
				return [$id, $text];
			}
		}
	}
}
;
class ParseException extends Exception {};
abstract class Parser extends FormatterPass {
	protected $filename = '';
	protected $debug = false;

	public function __construct($filename, $debug) {
		$this->filename = $filename;
		$this->debug = $debug;
	}

	protected function accumulateAndStopAtAny(&$tkns, $tknids, $ignoreList = []) {
		if (empty($ignoreList)) {
			$ignoreList[T_WHITESPACE] = true;
		} else {
			$ignoreList = array_flip($ignoreList);
		}
		$tknids = array_flip($tknids);
		$ret = '';
		$id = null;
		$text = null;
		while (list($index, $token) = each($tkns)) {
			list($id, $text) = $this->getToken($token);
			$this->ptr = $index;
			if (isset($ignoreList[$id])) {
				continue;
			}
			if (isset($tknids[$id])) {
				break;
			}
			$ret .= $text;
		}
		return [$ret, $id, $text];
	}

	public function candidate($source, $foundTokens) {
		return true;
	}

	protected function debug($msg) {
		$this->debug && fwrite(STDERR, $msg . PHP_EOL);
	}

	protected function detectsNamespace() {
		$namespace = '';
		while (list($index, $token) = each($this->tkns)) {
			list($id, $text) = $this->getToken($token);
			$this->ptr = $index;
			switch ($id) {
				case T_NAMESPACE:
					list($namespace, $foundId) = $this->accumulateAndStopAtAny($this->tkns, [ST_SEMI_COLON, ST_CURLY_OPEN], $this->ignoreFutileTokens);
					if ('{' == $foundId) {
						throw new ParseException("Namespaces with curly braces are not yet supported.");
					}
					break 2;
			}
		}
		if ('\\' == substr($namespace, 0, -1)) {
			$namespace = substr($namespace, 0, -1);
		}
		$namespace .= '\\';
		return $namespace;
	}

	public function format($source) {
		return $source;
	}

	abstract public function parse($source);

	protected function walkAndAccumulateCurlyBlock() {
		$tokens = [];
		$count = 1;
		while (list($index, $token) = each($this->tkns)) {
			list($id, $text) = $this->getToken($token);
			$this->ptr = $index;
			$this->cache = [];
			$tokens[] = [$id, $text];

			if (ST_CURLY_OPEN == $id) {
				++$count;
			}
			if (T_CURLY_OPEN == $id) {
				++$count;
			}
			if (T_DOLLAR_OPEN_CURLY_BRACES == $id) {
				++$count;
			}
			if (ST_CURLY_CLOSE == $id) {
				--$count;
			}
			if (0 == $count) {
				break;
			}
		}
		return $tokens;
	}
};
class ClassParser extends Parser {
	public function parse($source) {
		$parsedClasses = [];
		$parsedExtendedClasses = [];
		$parsedImplementedClasses = [];
		$this->tkns = token_get_all($source);
		$this->code = '';

		$namespace = $this->detectsNamespace();
		reset($this->tkns);
		while (list($index, $token) = each($this->tkns)) {
			list($id, $text) = $this->getToken($token);
			$this->ptr = $index;
			switch ($id) {
				case T_INTERFACE:
				case T_CLASS:
					if ($this->leftUsefulTokenIs(T_DOUBLE_COLON)) {
						continue;
					}
					$className = null;
					$extends = null;
					$implements = null;

					list($className, $foundId) = $this->accumulateAndStopAtAny($this->tkns, [ST_CURLY_OPEN, T_EXTENDS, T_IMPLEMENTS], $this->ignoreFutileTokens);

					if (T_EXTENDS == $foundId) {
						list($extends, $foundId) = $this->accumulateAndStopAtAny($this->tkns, [ST_CURLY_OPEN, T_IMPLEMENTS], $this->ignoreFutileTokens);
					}

					if (T_IMPLEMENTS == $foundId) {
						list($implements) = $this->accumulateAndStopAtAny($this->tkns, [ST_CURLY_OPEN], $this->ignoreFutileTokens);
					}

					$this->debug('[' . $className . ' e:' . $extends . ' i:' . $implements . ']');
					$parsedClasses[$namespace . $className][] = [
						'filename' => $this->filename,
						'extends' => $extends,
						'implements' => $implements,
					];
					if (!empty($extends)) {
						$parsedExtendedClasses[$extends] = [
							'filename' => $this->filename,
							'extended_by' => $className,
							'implements' => $implements,
						];
					}
					if (!empty($implements)) {
						$implements = explode(',', $implements);
						foreach ($implements as $implement) {
							$parsedImplementedClasses[$implement] = [
								'filename' => $this->filename,
								'implemented_by' => $className,
								'extends' => $extends,
							];
						}
					}
					break;
			}
		}
		return [
			$parsedClasses,
			$parsedExtendedClasses,
			$parsedImplementedClasses,
		];
	}
};
class ClassMethodParser extends Parser {
	public function parse($source) {
		$this->tkns = token_get_all($source);
		$this->code = '';

		$foundMethods = [];
		$namespace = $this->detectsNamespace();
		reset($this->tkns);
		while (list($index, $token) = each($this->tkns)) {
			list($id, $text) = $this->getToken($token);
			$this->ptr = $index;
			switch ($id) {
				case T_CLASS:
					if ($this->leftUsefulTokenIs(T_DOUBLE_COLON)) {
						continue;
					}

					list($className, $foundId, $foundText) = $this->accumulateAndStopAtAny($this->tkns, [ST_CURLY_OPEN, T_EXTENDS, T_IMPLEMENTS], $this->ignoreFutileTokens);
					if (T_EXTENDS == $foundId) {
						list(, $foundId, $foundText) = $this->accumulateAndStopAtAny($this->tkns, [ST_CURLY_OPEN, T_IMPLEMENTS], $this->ignoreFutileTokens);
					}

					if (T_IMPLEMENTS == $foundId) {
						list(, $foundId, $foundText) = $this->accumulateAndStopAtAny($this->tkns, [ST_CURLY_OPEN], $this->ignoreFutileTokens);
					}

					$classBody = array_merge([[$foundId, $foundText]], $this->walkAndAccumulateCurlyBlock());
					$foundMethods[$namespace . $className] = $this->parseMethods($namespace, $className, $classBody);
					break;
			}
		}
		return $foundMethods;
	}
	private function parseMethods($namespace, $className, $tokens) {
		$methodList = [];
		while (list(, $token) = each($tokens)) {
			list($id, $text) = $this->getToken($token);
			switch ($id) {
				case T_FUNCTION:
					list($functionName, $foundId, $foundText) = $this->accumulateAndStopAtAny($tokens, [ST_PARENTHESES_OPEN], $this->ignoreFutileTokens);
					if (empty($functionName)) {
						break;
					}

					if ("__construct" == $functionName) {
						$functionName = $className;
						$functionCall = $className;
						$functionSignature = $className . '(';
					} else {
						$functionCall = $functionName . $foundText;
						$functionSignature = $functionName . $foundText;
					}

					while (list(, $token) = each($tokens)) {
						list($id, $text) = $this->getToken($token);
						if (T_WHITESPACE == $id) {
							continue;
						}
						if (T_VARIABLE == $id) {
							$functionSignature .= ' ';
							$functionCall .= ' ';
						}
						if (T_VARIABLE == $id || ',' == $text || '(' == $text || ')' == $text) {
							$functionCall .= $text;
						}
						if (ST_CURLY_OPEN == $id || ST_SEMI_COLON == $id) {
							break;
						}
						$functionSignature .= $text;
					}
					$methodList[] = [
						$functionName,
						str_replace('( ', '(', $functionCall),
						str_replace('( ', '(', $functionSignature),
					];
					break;
			}
		}
		return $methodList;
	}

};
class ClassInstantiationsParser extends Parser {
	public function parse($source) {
		$uses = [];
		$this->tkns = token_get_all($source);
		$this->code = '';
		$namespace = $this->detectsNamespace();
		reset($this->tkns);
		while (list($index, $token) = each($this->tkns)) {
			list($id, $text) = $this->getToken($token);
			$this->ptr = $index;
			switch ($id) {
				case T_USE:
					if ($this->rightUsefulTokenIs('(')) {
						continue;
					}
					list($class, $id) = $this->accumulateAndStopAtAny($this->tkns, [T_AS, ';'], [T_WHITESPACE, T_COMMENT, T_DOC_COMMENT]);
					if (';' == $id) {
						$alias = substr(strrchr($class, '\\'), 1);
						$uses[$alias] = $class;
					} elseif (T_AS == $id) {
						list($alias) = $this->accumulateAndStopAtAny($this->tkns, [';'], [T_WHITESPACE, T_COMMENT, T_DOC_COMMENT]);
						$uses[$alias] = $class;
					}
			}
		}

		reset($this->tkns);
		$used = [];
		while (list($index, $token) = each($this->tkns)) {
			list($id, $text) = $this->getToken($token);
			$this->ptr = $index;
			switch ($id) {
				case T_NEW:
					if ($this->rightUsefulTokenIs(T_NS_SEPARATOR)) {
						// TODO! Analyse FQNs
						continue;
					}
					list($called) = $this->accumulateAndStopAtAny($this->tkns, ['('], [T_WHITESPACE, T_COMMENT, T_DOC_COMMENT]);
					if (isset($uses[$called])) {
						$used[$called] = $uses[$called];
					}
			}
		}
		return array_flip($used);
	}
};

function flushDb($uri, $fnDb, $ignoreList) {

	file_exists($fnDb) && unlink($fnDb);
	$db = new SQLite3($fnDb);
	$db->exec(
		'CREATE TABLE classes (
			filename text,
			class text,
			extends text,
			implements text
		);'
	);
	$db->exec(
		'CREATE TABLE extends (
			filename text,
			extends text,
			extended_by text,
			implements text
		);'
	);
	$db->exec(
		'CREATE TABLE implements (
			filename text,
			implements text,
			implemented_by text,
			extends text
		);'
	);
	$db->exec(
		'CREATE TABLE methods (
			filename text,
			class text,
			method_name text,
			method_call text,
			method_signature text
		);'
	);
	$db->exec(
		'CREATE TABLE calls (
			filename text,
			called text
		);'
	);

	fwrite(STDERR, "Database not found... generating" . PHP_EOL);
	$debug = false;

	$dir = new RecursiveDirectoryIterator($uri);
	$it = new RecursiveIteratorIterator($dir);
	$files = new RegexIterator($it, '/^.+\.php$/i', RecursiveRegexIterator::GET_MATCH);
	$all_classes = [];
	$all_extends = [];
	$all_implements = [];
	$all_methods = [];
	foreach ($files as $file) {
		$file = $file[0];
		foreach ((array) $ignoreList as $ignore) {
			$ignore = trim($ignore);
			if (
				substr(str_replace(getcwd() . '/', '', $file), 0, strlen($ignore)) == $ignore ||
				substr($file, 0, strlen($ignore)) == $ignore
			) {
				continue 2;
			}
		}
		echo $file;

		$content = file_get_contents($file);

		try {
			list($class, $extends, $implements) = (new ClassParser($file, $debug))->parse($content);
			$methods = (new ClassMethodParser($file, $debug))->parse($content);
			$calls = (new ClassInstantiationsParser($file, $debug))->parse($content);

			foreach ($calls as $class_name => $class_alias) {
				$db->exec('
					INSERT INTO
						calls
					VALUES
						(
							"' . SQLite3::escapeString($file) . '",
							"' . SQLite3::escapeString($class_name) . '"
						);
				');
			}

			foreach ($class as $class_name => $class_data) {
				foreach ($class_data as $data) {
					$db->exec('
					INSERT INTO
						classes
					VALUES
						(
							"' . SQLite3::escapeString($file) . '",
							"' . SQLite3::escapeString($class_name) . '",
							"' . SQLite3::escapeString($data['extends']) . '",
							"' . SQLite3::escapeString($data['implements']) . '"
						);
					');
				}
			}

			foreach ($extends as $extends_name => $data) {
				$db->exec('
				INSERT INTO
					extends
				VALUES
					(
						"' . SQLite3::escapeString($file) . '",
						"' . SQLite3::escapeString($extends_name) . '",
						"' . SQLite3::escapeString($data['extended_by']) . '",
						"' . SQLite3::escapeString($data['implements']) . '"
					);
				');
			}

			foreach ($implements as $implements_name => $data) {
				$db->exec('
				INSERT INTO
					implements
				VALUES
					(
						"' . SQLite3::escapeString($file) . '",
						"' . SQLite3::escapeString($implements_name) . '",
						"' . SQLite3::escapeString($data['implemented_by']) . '",
						"' . SQLite3::escapeString($data['extends']) . '"
					);
				');
			}

			foreach ($methods as $class => $class_methods) {
				foreach ($class_methods as $data) {
					$db->exec("
					INSERT INTO
						methods
					VALUES
						(
							'" . SQLite3::escapeString($file) . "',
							'" . SQLite3::escapeString($class) . "',
							'" . SQLite3::escapeString($data[0]) . "',
							'" . SQLite3::escapeString($data[1]) . "',
							'" . SQLite3::escapeString($data[2]) . "'
						);
					");
				}
			}
			echo ' done', PHP_EOL;
		} catch (ParseException $pe) {
			echo ' skipped - ' . $pe->getMessage() . PHP_EOL;
		}
	}
	$db->close();
};

if (!isset($argv[1])) {
	exit(255);
}
$cmd = trim(strtolower($argv[1]));
$ignoreList = [];
$ignoreListFn = 'oracle.ignore';
if (file_exists($ignoreListFn)) {
	$ignoreList = file($ignoreListFn);
}

if (!isset($fnDb)) {
	$fnDb = 'oracle.sqlite';
}

if (!file_exists($fnDb) || 'flush' == $cmd) {
	$uri = $argv[2];
	flushDb($uri, $fnDb, $ignoreList);
	exit(0);
}
if (time() - filemtime($fnDb) > 86400) {
	fwrite(STDERR, "Warning: database file older than a day" . PHP_EOL);
}

$db = new SQLite3($fnDb);

function introspectInterface(&$found_implements) {
	foreach ($found_implements as $row) {
		echo "\t", $row['implemented_by'], " - ", $row["filename"], PHP_EOL;
	}
	echo PHP_EOL;
}
if ("implements" == $cmd) {
	$results = $db->query("SELECT * FROM implements WHERE implements LIKE '%" . SQLite3::escapeString($argv[2]) . "'");
	$found_implements = [];
	while ($row = $results->fetchArray()) {
		$found_implements[] = [
			'filename' => $row['filename'],
			'implemented_by' => $row['implemented_by'],
		];
	}
	if (empty($found_implements)) {
		fwrite(STDERR, "Interface not found: " . $argv[2] . PHP_EOL);
		exit(255);
	}
	echo $argv[2] . ' implemented by' . PHP_EOL;
	introspectInterface($found_implements);
}

function introspectExtends(&$found_extends) {
	foreach ($found_extends as $row) {
		echo "\t", $row['extended_by'], " - ", $row["filename"], PHP_EOL;
	}
	echo PHP_EOL;
}
if ("extends" == $cmd) {
	$results = $db->query("SELECT * FROM extends WHERE extends LIKE '%" . SQLite3::escapeString($argv[2]) . "'");
	$found_extends = [];
	while ($row = $results->fetchArray()) {
		$found_extends[] = [
			'filename' => $row['filename'],
			'extended_by' => $row['extended_by'],
		];
	}
	if (empty($found_extends)) {
		fwrite(STDERR, "Class not found: " . $argv[2] . PHP_EOL);
		exit(255);
	}

	echo $argv[2] . ' extended by' . PHP_EOL;
	introspectExtends($found_extends);
}

function introspectClass(&$found_classes) {
	if (!empty($found_classes['extends'])) {
		echo "\t extends ", $found_classes['extends'], PHP_EOL;
	}

	if (!empty($found_classes['implements'])) {
		echo "\t implements ", $found_classes['implements'], PHP_EOL;
	}

	echo PHP_EOL;
}
if ("class" == $cmd) {
	$results = $db->query("SELECT * FROM classes WHERE class LIKE '%" . SQLite3::escapeString($argv[2]) . "'");
	$found_classes = [];
	while ($row = $results->fetchArray()) {
		$found_classes = [
			'filename' => $row['filename'],
			'class' => $row['class'],
			'extends' => $row['extends'],
			'implements' => $row['implements'],
		];
		break;
	}

	if (empty($found_classes)) {
		fwrite(STDERR, "Class not found: " . $argv[2] . PHP_EOL);
		exit(255);
	}

	echo $argv[2], PHP_EOL;
	introspectClass($found_classes);
}

function introspectCall(&$found_calls) {
	foreach ($found_calls as $row) {
		echo "\t ", $row['filename'], ' called ', $row['called'], PHP_EOL;
	}
	echo PHP_EOL;
}
if ("calls" == $cmd) {
	$results = $db->query("SELECT * FROM calls WHERE called LIKE '%" . SQLite3::escapeString($argv[2]) . "'");
	$found_calls = [];
	while ($row = $results->fetchArray()) {
		$found_calls[] = [
			'filename' => $row['filename'],
			'called' => $row['called'],
		];
	}

	if (empty($found_calls)) {
		fwrite(STDERR, "Call not found: " . $argv[2] . PHP_EOL);
		exit(255);
	}

	echo $argv[2], PHP_EOL;
	introspectCall($found_calls);
}
if ("introspect" == $cmd) {
	$target = $argv[2];

	$results = $db->query("SELECT * FROM implements WHERE implements LIKE '%" . SQLite3::escapeString($target) . "'");
	$all_found_implements = [];
	while ($row = $results->fetchArray()) {
		$all_found_implements[$row['implements']][] = [
			'filename' => realpath($row['filename']),
			'implemented_by' => $row['implemented_by'],
		];
	}
	foreach ($all_found_implements as $implements => $found_implements) {
		echo $implements . ' implemented by' . PHP_EOL;
		introspectInterface($found_implements);
	}

	$results = $db->query("SELECT * FROM extends WHERE extends LIKE '%" . SQLite3::escapeString($target) . "'");
	$all_found_extends = [];
	while ($row = $results->fetchArray()) {
		$all_found_extends[$row['extends']][] = [
			'filename' => realpath($row['filename']),
			'extended_by' => $row['extended_by'],
		];
	}
	foreach ($all_found_extends as $extends => $found_extends) {
		echo $extends . ' extended by' . PHP_EOL;
		introspectExtends($found_extends);
	}

	$results = $db->query("SELECT * FROM classes WHERE class LIKE '%" . SQLite3::escapeString($target) . "'");
	while ($row = $results->fetchArray()) {
		$found_classes = [[
			'filename' => realpath($row['filename']),
			'class' => $row['class'],
			'extends' => $row['extends'],
			'implements' => $row['implements'],
		]];
		echo "class " . $row['class'], PHP_EOL;
		introspectClass($found_classes);
	}

	ob_start();
	$foundMethod = false;
	$results = $db->query("SELECT * FROM methods WHERE method_name LIKE '%" . SQLite3::escapeString($target) . "'");
	while ($row = $results->fetchArray()) {
		$foundMethod = true;
		echo ' - ' . $row['class'] . '::' . $row['method_signature'], PHP_EOL;
	}
	$methodOutput = ob_get_clean();
	if ($foundMethod) {
		echo "Methods", PHP_EOL, $methodOutput;
	}

	$results = $db->query("SELECT * FROM calls WHERE called LIKE '%" . SQLite3::escapeString($target) . "'");
	$found_calls = [];
	while ($row = $results->fetchArray()) {
		$found_calls[] = [
			'filename' => realpath($row['filename']),
			'called' => $row['called'],
		];
	}
	echo PHP_EOL, "Calls " . PHP_EOL;
	introspectCall($found_calls);
}

if ("calltip" == $cmd) {
	ob_start();
	$foundMethod = false;
	$results = $db->query("SELECT * FROM methods WHERE method_name LIKE '%" . SQLite3::escapeString($argv[2]) . "'");
	while ($row = $results->fetchArray()) {
		$foundMethod = true;
		echo $row['class'] . '::' . $row['method_signature'], PHP_EOL;
		break;
	}
	$methodOutput = ob_get_clean();
	if ($foundMethod) {
		echo $methodOutput;
	}
}

if ("autocomplete" == $cmd) {
	$searchFor = $argv[2];

	echo "term,match,class,type\n";

	$results = $db->query("SELECT * FROM classes WHERE class LIKE '%" . SQLite3::escapeString($searchFor) . "%' ORDER BY class");
	while ($row = $results->fetchArray()) {
		$tmp = explode('\\', $row['class']);
		fputcsv(STDOUT, [$row['class'], array_pop($tmp), $row['class'], 'class'], ',', '"');
	}
	$results = $db->query("SELECT * FROM classes WHERE class LIKE '%" . SQLite3::escapeString($searchFor) . "' ORDER BY class");
	while ($row = $results->fetchArray()) {
		$tmp = explode('\\', $row['class']);
		fputcsv(STDOUT, [$row['class'], array_pop($tmp), $row['class'], 'class'], ',', '"');
	}
	$results = $db->query("SELECT * FROM methods WHERE method_name LIKE '%" . SQLite3::escapeString($searchFor) . "%'");
	while ($row = $results->fetchArray()) {
		fputcsv(STDOUT, [$row['method_call'], $row['method_signature'], $row['class'], 'method'], ',', '"');
	}
}