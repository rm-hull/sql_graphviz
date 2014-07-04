# SQL Graphviz

SQL Graphvis is a small python script that generates a [Graphviz](http://www.graphviz.org/)
visualization of a SQL schema dump.

### Usage

Using PostgreSQL, for example, to generate as a PNG file:

    $ pg_dump --schema-only dbname | python sql_graphviz.py | dot -Tpng > graph.png

The program will accept a named file, or if omitted as above, will take from stdin.
Output to SVG:

    $ pg_dump --schema-only dbname > dump.sql
    $ python sql_graphviz.py dump.sql > graph.dot
    $ dot -Tsvg graph.dot > graph.svg

### Example

![SVG](https://rawgithub.com/rm-hull/sql_graphviz/master/example.svg)

## Credits

Extended from http://energyblog.blogspot.co.uk/2006/04/blog-post_20.html by [EnErGy [CSDX]](https://www.blogger.com/profile/09096585177254790874)

## The MIT License (MIT)

Copyright (c) 2014 Richard Hull & EnErGy [CSDX]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
