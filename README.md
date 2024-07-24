# publicBAP-GPT
RAG Chatbot model retrieving the national policies and procedures from Beta Alpha Psi along with custom data uploads. 


## Upload Your Own Information
PDF Docs are searched and retrieved in the "/documents/" folder. If you wish to upload your own documents for retreval please upload them into the "/documents/" folder and push the changes to your git repo. 



## Customize Your Bot
If you wish the make changes to the icons displayed under the student and BAP-GPT output then that you will want to go to the htmlTemplates.py file and find line 31 and line 40 in the file. The URls included in this file are links to the webite i.ibb.co. This platform allows you to upload images and get the url for this image to be referenced. Be sure to use the HTML link. 

If you would like to tinker with the length of text chunks for improved response accuracy. You can find the area to do that in the file app.py under the function "get_text_chunks" (line 55-63). Chunk_size is the charater length of the chunks your are parsing. Chunk_overlap is the amount of the last chunk that will be included in the following chunk, this is used to eliminate the possibility of missing information when breaking the text into chunks. Simply change the integer that is shown with one of your own and push to the git repo. 



