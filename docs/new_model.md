Each entity will have an id, which is an integer and primary key for the table, however, when you insert an entity, sqlalchemy automatically generate next integer for you. So the primary key is hidden.


Usually the label within one entity domain is unqiue. For example, for the nodes, you only have one and only one label "death-star-101".But for the NICs,there are only a few labels, (ipmi, pxe, data1,..etc) They are not unique identifiers.


Each relationship requires a foreign key, however, you only have to declare in one of the two related table, the other table will get the replationship by "backref". For one-to-many, many-to-one mapping, specifying the foreign key is sufficient. However, for many-to-many mapping (User to Group mapping), you also need specify a secondary table which has two column, one of the primary key of the left table, the other is of the right table. 


Node
    id, label, available, project_label(foreign key, many to one mapping to project)
    
    
Project
    id, label, deployed(boolean), group_label(foreign key, many to one mapping to group)


Group
    id, label


Users
    id, label(username), password, group_label(foreign key, many to many mapping to group)

     




There is lot of boilerplate code in the model.py on devel branch. I'm trying to refactor it.(meta-programming?)
