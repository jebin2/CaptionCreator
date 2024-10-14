import { serve } from "bun";
import { Database } from "sqlite-async";
import { readFile } from "fs/promises";
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
  uploadedToYoutube: boolean;
  uploadedToX: boolean;
};

// Create and initialize the database
async function initDatabase() {
  const db = await Database.open("entries.db");
  await db.run(`
    CREATE TABLE IF NOT EXISTS entries (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      audioPath TEXT NOT NULL,
      title TEXT NOT NULL,
      description TEXT NOT NULL,
      thumbnailText TEXT NOT NULL,
      answer TEXT NOT NULL,
      generatedVideoPath TEXT,
      generatedThumbnailPath TEXT,
      uploadedToYoutube INTEGER DEFAULT 0,
      uploadedToX INTEGER DEFAULT 0
    )
  `);
  return db;
}

let dbPromise = initDatabase();

serve({
  async fetch(req) {
    const url = new URL(req.url);
    const { pathname } = url;

    // Handle GET request for the main page
    if (req.method === "GET" && pathname === "/") {
      const htmlFilePath = path.join(process.cwd(), 'views', 'index.html');
      const htmlContent = await readFile(htmlFilePath, "utf-8");
      return new Response(htmlContent, {
        headers: { "Content-Type": "text/html" },
      });
    } 
    // Handle POST request to submit new entry
    else if (req.method === "POST" && pathname === "/submit") {
      const db = await dbPromise;
      return req.formData().then(async data => {
        const audioPath = data.get("audioPath") as string;
        const title = data.get("title") as string;
        const description = data.get("description") as string;
        const thumbnailText = data.get("thumbnailText") as string;
        const answer = data.get("answer") as string;

        // For this example, we're assuming the video and thumbnail paths are generated later
        const generatedVideoPath = null; // Placeholder for generated video path
        const generatedThumbnailPath = null; // Placeholder for generated thumbnail path
        const uploadedToYoutube = false; // Set to false for demo purposes
        const uploadedToX = false; // Set to false for demo purposes

        await db.run(`
          INSERT INTO entries (audioPath, title, description, thumbnailText, answer, generatedVideoPath, generatedThumbnailPath, uploadedToYoutube, uploadedToX)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`, 
          [audioPath, title, description, thumbnailText, answer, generatedVideoPath, generatedThumbnailPath, uploadedToYoutube ? 1 : 0, uploadedToX ? 1 : 0]);

        return new Response("Entry submitted successfully!", { status: 201 });
      });
    } 
    // Handle DELETE request to remove an entry
    else if (req.method === "DELETE" && pathname.startsWith("/delete/")) {
      const id = pathname.split("/").pop();
      const db = await dbPromise;
      await db.run(`DELETE FROM entries WHERE id = ?`, [id]);
      return new Response("Entry deleted successfully!", { status: 204 });
    }
    // Handle GET request for entries
    else if (req.method === "GET" && pathname === "/entries") {
      const db = await dbPromise;
      const entries: Entry[] = await db.all("SELECT * FROM entries");
      return new Response(JSON.stringify(entries), {
        headers: { "Content-Type": "application/json" },
      });
    }
    return new Response("Not Found", { status: 404 });
  },
});

console.log("Running on... http://localhost:3000");