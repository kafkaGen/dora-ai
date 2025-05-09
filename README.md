## How to use

0. install dependencies with poetry
1. update the .env file as in .env.example
2. run `make start-database` to start the database (wait until it's ready)
3. run `make load-data-neo4j` to load the data into the neo4j database
4. run `make query-rag` to query the database (print logs in console and return answer as script output)
