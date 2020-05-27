# Congist

## INTRODUCTION

**Congist** is a gist manager.

Currently it is a Python API and command-line client which supports
create, read, update, and delete (CRUD) operations on GitHub gist.

## INSTALLATION

1. Clone this repository in a terminal and change to the project directory.

2. Obtain an access token from [GitHub](https://github.com/settings/tokens).

3. Copy data/user_sample.yml to user's home directory, rename it to .congist in
a POSIX system (e.g. Unix, Linux, Mac OS X) or \_congist in a non-POSIX
system(e.g. Windows).

4. Edit .congist/\_congist to fill out your GitHub username and access_token
with the values you've just got in step 2.

5. Run the `make install` in the terminal, and it will generate a script file
`build/congist.sh`.

6. Move the above script file to anywhere in your system PATH.

7. Run `congist.sh -h` to show help information and all available sub-commands.

8. Run `congist.sh <sub-command> -h` to show a sub-command's help information.

## REFERENCE

[GitHub API V3 documentation](http://developer.github.com/v3/gist)

## LICENSE

Copyright 2020-2021 Hui Zheng

Released under the [MIT License](http://www.opensource.org/licenses/mit-license.php).
