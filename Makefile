start-database:
	docker compose --env-file .env -f docker/docker-compose.yaml -p dora_ai up -d

load-data-neo4j:
	@printf "CREATE CONSTRAINT FOR (n:AppState) REQUIRE n.neo4jImportId IS UNIQUE;\nCALL apoc.import.json(\"file:///graph_export.json\", {createRelationships: true, batchSize: 10000});\n" | docker exec -i neo4j cypher-shell -u neo4j -p neo4j_password
