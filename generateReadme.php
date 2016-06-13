<?php
$str = file_get_contents(__DIR__ . '/README.src.md');

$commands = json_decode(file_get_contents(__DIR__ . '/Default.sublime-commands'), true);

$cmd = sprintf("php %s/fmt.phar --list-simple", __DIR__);
$passes = explode(PHP_EOL, trim(`$cmd`));

$strCommands = implode(PHP_EOL,
    array_map(function ($v) {
        return ' *  ' . $v['caption'];
    }, $commands)
);

$strPasses = implode(PHP_EOL,
    array_map(function ($v) {
        return ' * ' . $v;
    }, $passes)
);

file_put_contents(__DIR__ . '/README.md',
    strtr($str, [
        '%CMD%'    => $strCommands,
        '%PASSES%' => $strPasses,
    ])
);