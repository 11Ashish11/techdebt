

### Where would you look first? Which file and function rank as the highest priority in the hotspot table, and what does the code inspection reveal?


-> The first file that I would look would be tabulate/__init__.py. This file ranks first in hotspot table and has the most complexity, duplication, and comments. 

-> The highest function that ranks is _normalize_tabular_data in th same file. (CC 76, rank F, 186 lines).


### Is the worst function really debt? Look at the top function by CC. Is it necessary domain complexity (e.g. many formats) or accidental complexity that should be refactored?


-> The worst fucntion is _normalize_tabular_data. This a mix I would say with some part is necessary domain complexity  and other can be refactored.

The necessary part includes - 
- The function's job is to accept many input shapes
- Accepting "anything table-like" is the library's main selling point

The part that can be refactored is - 
-  Header handling is repeated inside each type branch.
-  Unrelated steps share the function.
- The list-of-dicts branch alone is about 30 lines with its own nested loops and four-way header chain.

Conclusion - Yes this is debt but not all is debt.


### Do the signals agree? Do the TODO/FIXME comments and duplication sit in the same files as the high-complexity functions?

At the file level, yes. At the function level, only partly.

File level: everything points at __init__.py.
Complexity, SATD, Duplication and other metrics.

Function level: the signals mostly point at different places.
 TODO at line 1224 , 748, The reported duplication etc are different

 