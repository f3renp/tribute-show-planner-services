# Architecture Decision Records

## 1. Choose Flask and built-in sqlite3 over FastAPI and Django
Date: 2026-10-05
Status: Decided
Context: This assignment needs a small web app that runs as one process and gets containerised later. It has two domains and a handful of pages, and the brief requires SQLite for storage.
Decision: I chose Python with Flask for the web pages and Python's built-in sqlite3 so I can write the SQL queries myself. The app is served by waitress, which app.py starts, so "python app.py" is the only command needed.
Alternatives considered: I considered Django because I used it last semester in my Database class, but it comes with features this app does not need, such as the admin panel, and it needs a manual "python manage.py migrate" step before its tables exist, which conflicts with the brief's rule of no manual setup at startup. I also considered FastAPI, but it is designed for JSON APIs while this app serves HTML pages, and it has concepts I would have had to learn first. I did not add an ORM like SQLAlchemy because it is an extra package and it generates the SQL for me, so I could not explain those queries myself.
Consequences: I have to write myself what Django would have given me: the SQL queries, creating the tables at startup and form validation, and there is no ready-made login if I ever need one. But in return, the app depends on only 4 direct packages.

## 2. Keep catalogue and show builder as separate packages
Date: 2026-10-06
Status: Decided
Context: The brief requires two separate feature areas, the catalogue and the show builder, which could later become independent services. Because of that, they should not be too tightly connected.
Decision: The code will be split into two folders, catalogue/ and shows/. The show builder will only store a song_id and will ask the catalogue for the full song details when needed.
Alternatives considered: A simpler option was to put everything in one folder, or organise it only by type, such as keeping all database code together and all pages together. I rejected that because it would mix the two domains and make them harder to separate later.
Consequences: The cost is that the structure is slightly more complex and some communication between the two parts is needed. The benefit is that the code is cleaner and each domain can be changed or separated more easily later.

## 3. Setlist items reference songs by ID only
Date: 2026-10-08
Status: Decided
Context: The catalogue and show builder are separate domains, so a decision is needed about how setlists refer to songs without tightly coupling both parts.
Decision: setlist_items stores only the song_id, not the full song data. When the show builder needs the details, it asks the catalogue through two read-only functions, get_songs_by_ids() and list_active_songs().
Alternatives considered: The normal approach would be a foreign key from song_id to songs, or a SQL JOIN between the show and catalogue tables. It would make a future split into separate services harder because the songs table would then live in a different database, and a foreign key cannot point into another database.
Consequences: The cost is that the database can no longer guarantee that every song_id actually exists in songs. The benefit is that if the catalogue becomes a separate service later, the show builder can keep storing IDs and only the way it fetches song details would need to change.

## 4. Test rules and services first, keep routes thin
Date: 2026-10-10
Status: Decided
Context: The brief asked for at least 70% test coverage, so I focused on testing the parts of the program where the important decisions are made. I wanted to make sure the main rules of the app were properly checked.
Decision: I tested the six checks in shows/rules.py most thoroughly, reaching 100% coverage, and then tested the services and repositories, which are around 99-100%. I kept the routes thin because they do not contain the actual rules; they mainly call the services, run the checks, and pass the results to the pages.
Alternatives considered: I could have tested the web pages using Flask's test client as well. I did not make that the priority because the brief asks for coverage of the core business logic, and page tests would mostly check HTML and could break after visual changes even when the actual rules still work correctly.
Consequences: The downside is that the routes and app.py still have 0% coverage, so some page or routing problems might not be caught by the tests. The benefit is that the most important logic is well tested, the tests are fast, and the project now has 77% coverage of the app code, which is above the required 70%.

## 5. No login in this version
Date: 2026-10-11
Status: Decided
Context: The app is designed as a simple tool for one tribute act. The musical director and manager have different jobs, but they are still part of the same small trusted team. Because they trust each other, separate accounts and permissions are not necessary yet.
Decision: I decided not to build a login in this version.
Alternatives considered: I could have added something simple like one shared password for the whole app, or used a login library such as Flask-Login. One shared password would add very little because everyone would still use the same identity. It would not tell us who changed what, so it would not give much accountability. A full login with a library would add extra work without being necessary yet.
Consequences: Right now the app runs on a trusted machine or local network, so anyone with access to that network can view and change the catalogue and shows. A login would become necessary before deploying it somewhere like Azure where other people could access it, and that would mean adding user accounts, password handling, authentication, probably new database tables, and deciding which user can see or edit which shows and songs.
## 6. Split into a catalogue service and a shows service
Date: 2026-11-10
Status: Decided
Context: Assignment 2 asks for the app to run as separate services. ADR-2 and ADR-3 already kept the two domains apart, with the show builder reaching the catalogue only through get_songs_by_ids() and list_active_songs(), so that seam is the natural place to cut.
Decision: The code is split into services/catalogue and services/shows. Each one is its own Flask app with its own Dockerfile, requirements.txt, tests and SQLite file under DATA_DIR. The catalogue service owns the outfits and songs tables (catalogue.db) and keeps the demo seed. The shows service owns the shows and setlist_items tables (shows.db). The two seam functions became read-only JSON endpoints on the catalogue, GET /api/songs?ids=... and GET /api/songs/active, and the shows service calls them over HTTP from shows/catalogue_client.py, using the address in CATALOGUE_URL. Both services answer GET /health. docker-compose.yml starts both, with one named volume each.
Alternatives considered: I could have kept one database file and mounted it into both containers. I rejected that because both services could then read and write each other's tables, and the split would only exist in the folder names. I could also have kept the shows service importing the catalogue code, but then it could not be built or deployed on its own.
Consequences: The show page now depends on the catalogue being reachable: if it is down, the page fails, which is a TODO in catalogue_client.py. Every show page makes one or two HTTP calls instead of function calls. The links between the pages of the two services go through CATALOGUE_PUBLIC_URL and SHOWS_PUBLIC_URL, because the browser and the shows container reach the catalogue at different addresses. In return, each service has its own data, its own image and its own tests, and the shows tests use a fake catalogue instead of the real one.