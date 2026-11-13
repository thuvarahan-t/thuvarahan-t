# IN3101 Lab 02 - Library Book REST API

Name: Thuvarahan.T  
Index: 234210G

Spring Boot 4.1.1, Java 21, Spring Data JPA, MySQL and springdoc 3.1.1.

## Run
1. Run database.sql in MySQL.
2. Set DB_USER and DB_PASSWORD for your MySQL connection. Optional DB_URL defaults to jdbc:mysql://localhost:3306/library_db.
3. Run `mvn spring-boot:run`.
4. Open http://localhost:8080/swagger-ui.html.

## Test
Import 234210G.postman_collection.json into Postman. Start with an empty book table; create two books first, then run S1-S7 in order. S1 creates ID 3. The collection covers 201, 200, 204, 404 and 400. The title containing 234210G appears in S2.

Endpoints: GET/POST /api/books, GET/PUT/DELETE /api/books/{id}.

POST is documented with a summary and responses 201/400. Blank title/author and negative price are validated.

## Lab 03 — Run with Docker Compose

Use Java 21, Maven, and a running Docker Desktop. In PowerShell, from the repository root:

```powershell
Copy-Item .env.example .env
mvn clean package -DskipTests
docker compose up --build -d
docker compose ps
```

Set `DB_ROOT_PASSWORD` in your local `.env` before starting. The API listens on port 8080, and MySQL Workbench can connect to `127.0.0.1:3307` as `root` using the same password. Inside the Compose network the API connects to `db:3306`. Inside a standalone API container, `localhost` points to that container itself.

Open Swagger UI at <http://localhost:8080/swagger-ui.html>. Create three books through `POST /api/books`, including one titled `234210G - Clean Code`, then check the rows with `SELECT * FROM library_db.book;` in MySQL Workbench.

To check persistence, record the IDs from `GET /api/books`, run `docker compose down` and `docker compose up -d`, then repeat the GET after the API starts. The named volume keeps the books and IDs. The `-v` flag on `docker compose down` deletes that volume.
