# object-oriented-vis
Visualisation support for OO scan 


# Features 
(1) Identify all classes, methods, functions, and variables in a package 
(2) Identify classes reference between each others
    (a) inheritence 
    (b) method reference
(3) Scope the files that are included 
(4) runnable files to be included


# Architecture 
(1) Members of a group:
Define a group/family of a class as all the things that got referenced in that class/function/script. Theses can be:
- Class init 
- Type hint
- Method of an object got called 
- etc...

(2) What are the actors in the overview?
- functions 
- classes 
    - methods 
    - attributes
- executable code

(3) Type of references?
- Class references


# RelationshipManager 
- actors: classes 
- 2 tables:
    - actors: which class, function, method, script/module a node belong to 
    - Relationships: what is the relationship types


# OO design
- Repo manager: managing repo and all the modules or other types of file with tree under it 
    - Look for node when needed 
    - Look for all the def when asked for it 
- Node: res as wrapper around the ast.Node but also allow traverse up     
    - At node level allow the node to search for class, function, method, script/module upper 
- RelationshipManager: Determine the relationships between 2 particular nodes 
    - Different types of nodes
