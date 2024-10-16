import { serve } from "bun";
import { Database } from "sqlite-async";
import { readFile, copyFile } from "fs/promises";
import path from "path";

type Entry = {
	id: number;
	audioPath: string;
	title: string;
	description: string;
	thumbnailText: string;
	answer: string;
	generatedVideoPath: string | null;
	generatedThumbnailPath: string | null;
	uploadedToYoutube: number;
	uploadedToX: number;
	youtubeVideoId: string;
	tweetId: string;
};

// Logging function for structured logs
function log(message: string) {
	console.log(`[${new Date().toISOString()}] ${message}`);
}

// Create and initialize the database
async function initDatabase(alter = false) {  // Set default to false
	const db = await Database.open("entries.db");

	try {
		log("Initializing database...");

		// Create the table if it doesn't exist
		await db.run(`CREATE TABLE IF NOT EXISTS entries (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				audioPath TEXT NOT NULL,
				title TEXT NOT NULL,
				description TEXT NOT NULL,
				thumbnailText TEXT NOT NULL,
				answer TEXT NOT NULL,
				generatedVideoPath TEXT,
				generatedThumbnailPath TEXT,
				uploadedToYoutube INTEGER,
				uploadedToX INTEGER,
				youtubeVideoId TEXT,
				tweetId TEXT
			)`);

		log("Database initialized.");
		return db;
	} catch (error) {
		log("Error during database initialization: " + error);
		throw error;
	}
}

// Backup function
async function backupDatabase() {
	const source = path.join(process.cwd(), "entries.db");
	const destination = path.join(process.cwd(), "backup", `entries_backup.db`);

	try {
		await copyFile(source, destination);
		log(`Backup created: ${destination}`);
	} catch (error) {
		log("Error creating backup: " + error);
	}
}

let dbPromise = initDatabase();  // Default alter is false unless needed

serve({
	async fetch(req) {
		const url = new URL(req.url);
		const { pathname } = url;

		try {
			// Serve HTML file for the main page
			if (req.method === "GET" && pathname === "/") {
				log("Serving main page...");
				const htmlFilePath = path.join(process.cwd(), 'views', 'index.html');
				const htmlContent = await readFile(htmlFilePath, "utf-8");
				return new Response(htmlContent, {
					headers: { "Content-Type": "text/html" },
				});
			}

			// Handle POST request to submit new entry
			else if (req.method === "POST" && pathname === "/submit") {
				log("Handling entry submission...");
				const db = await dbPromise;
				return req.formData().then(async data => {
					const audioPath = data.get("audioPath") as string;
					const title = data.get("title") as string;
					const description = data.get("description") as string;
					const thumbnailText = data.get("thumbnailText") as string;
					const answer = data.get("answer") as string;

					// Placeholder for generated paths and uploaded status
					const generatedVideoPath = null;
					const generatedThumbnailPath = null;
					const uploadedToYoutube = 0; // Default to false, no upload yet
					const uploadedToX = 0; // Default to false, no upload yet

					await db.run(`INSERT INTO entries (audioPath, title, description, thumbnailText, answer, generatedVideoPath, generatedThumbnailPath, uploadedToYoutube, uploadedToX) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
						[audioPath, title, description, thumbnailText, answer, generatedVideoPath, generatedThumbnailPath, uploadedToYoutube, uploadedToX]);

					log("Entry submitted: " + JSON.stringify({ audioPath, title, description }));
					await backupDatabase();  // Create a backup after inserting an entry
					return new Response("Entry submitted successfully!", { status: 201 });
				});
			}

			// Handle DELETE request to remove an entry
			else if (req.method === "DELETE" && pathname.startsWith("/delete/")) {
				const id = pathname.split("/").pop();
				log(`Deleting entry with ID ${id}...`);
				const db = await dbPromise;
				await db.run(`DELETE FROM entries WHERE id = ?`, [id]);
				log(`Entry with ID ${id} deleted.`);
				await backupDatabase();  // Create a backup after deleting an entry
				return new Response("Entry deleted successfully!", { status: 204 });
			}

			// Handle GET request for entries (JSON)
			else if (req.method === "GET" && pathname === "/entries") {
				log("Fetching all entries...");
				const db = await dbPromise;
				const entries: Entry[] = await db.all("SELECT * FROM entries");
				log(`Fetched ${entries.length} entries.`);
				return new Response(JSON.stringify(entries), {
					headers: { "Content-Type": "application/json" },
				});
			}

			// Return 404 for any other paths
			log("Path not found: " + pathname);
			return new Response("Not Found", { status: 404 });

		} catch (error) {
			log("Error during request handling: " + error);
			return new Response("Internal Server Error", { status: 500 });
		}
	},
});

log("Server running on http://localhost:3000");
