PA#2 - Concurrent Hash Table
Ungraded, 100 Possible Points

Unlimited Attempts Allowed
Available until Apr 19, 2026 11:59pm
A concurrent hash table is a data structure that allows multiple threads to perform operations on a shared collection of key-data pairs, without causing data corruption or inconsistency. The concurrent hash table consists of a linked list of nodes, each of which stores some data associated with the key. The hash value is computed by applying a hash function to the key.

Note that for this assignment, we will not be taking into consideration hash collisions. We will use Jenkins's one_at_a_time hash functionLinks to an external site.

Links to an external site.Links to an external site. which has a very low collision rate for the number of hashes we will be working with. Regardless, your test data and the final data set you will be graded against will be guaranteed collision-free.

The concurrent hash table supports the following functions:

insert(key, values): This function inserts a new key-data pair into the hash table.  If the entry already exists, report an error. To insert a key-data pair, the function first computes the hash value of the given name (the key).  Then, it acquires the write lock that protects the list and searches the linked list for the hash.  It then creates a new node and inserts it in the list. Finally, it releases the write lock and returns.
delete(key): This function deletes a key-data pair from the hash table, if it exists. To delete a key-data pair, the function first computes the hash value of the key and obtains a writer lock. Then it searches the linked list for the key. If the key is found, it removes the node from the list and frees the memory. Otherwise, it does nothing. Finally, it releases the write lock and returns.
updateSalary(key, value): This function takes a key and an integer value.  If it finds a node with a matching key, it updates the salary field with the given value.
search(key): This function searches for a key-data pair in the hash table and returns the value, if it exists. To search for a key-data pair, the function first computes the hash value of the key acquires a reader lock. Then, it searches the linked list for the key. If the key is found, it returns the value. Otherwise, it returns NULL. Finally, it releases the read lock and returns. The caller should then print the record or "No Record Found" if the return is NULL.
The Hash Table Structure
typedef struct hash_struct
{
  uint32_t hash;
  char name[50];
  uint32_t salary;
  struct hash_struct *next;
} hashRecord;
Field	Description
hash	32-bit unsigned integer for the hash value produced by running the name text through the Jenkins one-at-a-time functionLinks to an external site.
name	Arbitrary string up to 50 characters long
salary	32-bit unsigned integer (who wants a negative salary, eh?) to represent an annual salary.
next	Pointer to the next record
Reader-Writer Lock Reference
The OSTEP authors have provided sample implementations that you should reference:

https://github.com/remzi-arpacidusseau/ostep-code/tree/master/threads-semaLinks to an external site.

The Command File
Your program must read a text file called commands.txt containing some configuration information, commands, and data values. Do not read it from the console. You should hard code "commands.txt" into your program.

List of Commands and their parameters
Command	Parameters	Description
insert	<name>,<salary>,<priority>	Inserts the data for the given name and salary value.
delete	<name>,<priority>	Name whose record is to be deleted from the list.
update	<name>,<new salary value>	Name whose record is to have its salary updated.
search	<name>,<priority>	Name whose record is to be retrieved and printed to the output file.
print	<priority>	Print the entire contents of the list to the output file.
Sample Command File
insert,Richard Garriot,40000,1  
insert,Sid Meier,50000,2  
insert,Shigeru Miyamoto,51000,3  
delete,Sid Meier,4  
insert,Hideo Kojima,45000,5  
insert,Gabe Newell,49000,6  
insert,Roberta Williams,45900,7  
delete,Richard Garriot,8  
insert,Carol Shaw,41000,9  
search,Sid Meier,10
Expected Output
Command Output
Output from the commands should be written to the console via stdout.

Each command will provide some form of user feedback as follows:

Command	Output
INSERT	
Inserted <values>
on Duplicate entry:  Insert failed.  Entry <hash> is a duplicate.

UPDATE	Updated record <hash> from <old values> to <new values>
on Missing entry:  Updated failed.  Entry <hash> not found.
DELETE	Deleted record for <values>
on Missing entry:  Entry <hash> not deleted.  Not in database.
SEARCH	Found: <values>
Not Found:  <search string> not found.
PRINT	Current Database:
<all records in the database, sorted by hash>
At the end of the run, you will need to run a final PRINT (to the console/stdout), even if the last command of the commands.txt file is PRINT.

NOTE:

Only the final list print is evaluated for grading purposes.  The exact ordering of thread execution will be random, as we've discussed in class.
The delete function may incur one or two sets of lock operations, depending on your implementation:
If you use the search function you already wrote to find the record to delete, you will have two sets of lock operations -- the outer lock for the delete and the inner one for the search.
Otherwise, you'll just have one set of operations.
Why Priority and Locking?  Rationale for Priority Ordering AND Mutual Exclusion
Log File (hash.log)
We also need diagnostic output to make sure that our locks and CVs are occurring as expected.

Write out each command as they're executed, along with their parameters in this format:
<timestamp>: THREAD <priority>,<command and parameters>

You will also write out when locks are acquired and released:
<timestamp>: THREAD <priority>WAITING FOR MY TURN
<timestamp>: THREAD <priority>AWAKENED FOR WORK
<timestamp>: THREAD <priority>READ LOCK ACQUIRED
<timestamp>: THREAD <priority>READ LOCK RELEASED
<timestamp>: THREAD <priority>WRITE LOCK ACQUIRED
<timestamp>: THREAD <priority>WRITE LOCK RELEASED

Use the following function to obtain accurate timing values:

#include "`sys/time.h"

long long current_timestamp() {  
  struct timeval te;  
  gettimeofday(&te, NULL); // get current time  
  long long microseconds = (te.tv_sec * 1000000) + te.tv_usec; // calculate milliseconds  
  return microseconds;  
} 
Sample log output looks something like this:

1721428978841092: THREAD 0 INSERT,2569965317,Hideo Kojima,45000   
1721428978841096: THREAD 0 WRITE LOCK ACQUIRED   
1721428978841098: THREAD 0 WRITE LOCK RELEASED
Final Deliverables:
Filename	Purpose
chash.c	Your main program that reads the commands.txt and produces output to the console
Makefile	Your Makefile that builds this project into the final executable.  Make your code modular, use multiple source files!
Other Source Files	Any additional source files that you used in your program.  Please don't write a monolithic chash.c!
README.txt	Use for anything I or my graders need to know and the AI use citation (see below)
All of these should be uploaded as a single zip file containing all of the files.
We should be able to:
Unzip your file.
Run make to compile it into the main executable chash
Your program will read commands.txt and then produce hash.log and console output for the product of each command.
Sample Input and Output Files
Sample Input:  commands_comprehensive_test.txtDownload commands_comprehensive_test.txt

Sample Output:  PA#2 Expected Output

Sample Log:  hash.logDownload hash.log

AI Policy
When using AI assistants, please adhere to the following policies and suggestions:

Put Effort into Crafting High-Quality Prompts: Tools like ChatGPT and CoPilot, while useful, have serious limitations, and hence are often incorrect. If you provide minimum effort prompts, you will get low quality results. You will need to refine your prompts in order to get good outcomes. This will take concerted effort.
Be Aware of AI Limitations: Even if you have crafted well-constructed prompts, do not blindly trust anything an AI assistant tool says or outputs. If it gives a snippet of code, number, or fact, assume that it is wrong unless you either know it to be correct or check it with another source. You are responsible for any errors or omissions provided by the tool, and these tools tend to work best for topics you fully understand.
Give the AI Tool Proper Attribution: AI is a tool, and one that you must acknowledge using. Thus, you must provide these tools proper attribution if you use them for assignments. As such, you are required to provide a paragraph or two either in a comment or in the README file explaining what you used the AI for, and what prompts you used to get the results. Failure to do this will result in a violation of UCF Academic Integrity policies.
Know When to Use and Not Use AI Tools Be thoughtful about when AI tools are useful and when they are not. Don't use the tool if it isn't appropriate, or if you do not have full grasp of a given concept from class.
credit to Dr. Kevin Moran for this succinct summary of AI use policy!

Extra Credit
For extra credit, you may choose to implement this assignment in Rust with one major new requirement:

You must document your project for me as if I were a complete Newb to Rust (which I am).

In other words, use this project as a teaching example.  Specific things I'm looking for are the thread- and memory-safe features of Rust.
Explain them and how you used them in your project.
Any place where Rust differs significantly from C should be pointed out as well.

Documentation should be in a separate file, preferably NOT the README.  The README is reserved for build and run instructions and your AI citation(s).
Ideally, the documentation should be in Markdown.  If you give me a Word file or a PDF, I will probably cry, but I will accept it.
Total Points Available:  10.

Concurrent Hash Rubric
Concurrent Hash Rubric
Criteria	Ratings	Points
Compiles
view longer description

Full Marks
5 pts

No Marks
0 pts
/5 pts
Runs to Completion
view longer description

Full Marks
5 pts

No Marks
0 pts
/5 pts
Correctly Inserts into the Hash Table
view longer description

Full Marks
5 pts

No Marks
0 pts
/5 pts
Correctly Deletes Records from the Hash Table

Full Marks
5 pts

No Marks
0 pts
/5 pts
Correctly Prints the Entire Hash Table on a print command
view longer description

Full Marks
5 pts

No Marks
0 pts
/5 pts
Lock Messages are Printed

Full Marks
5 pts

No Marks
0 pts
/5 pts
Lock and Unlock Occur as Expected
view longer description

Full Marks
20 pts

No Marks
0 pts
/20 pts
Correctly Searches for Names in the Hash Table and prints the record

Full Marks
5 pts

No Marks
0 pts
/5 pts
Correctly Updates Salary Data
view longer description

Full Marks
5 pts

No Marks
0 pts
/5 pts
Test Case Completion (8 Tests, 5 pts each)
view longer description

Full Marks
40 pts

No Marks
0 pts
/40 pts