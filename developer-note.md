**Tilas: Quick Note-Taking Web App**

**Overview**

Tilas is a web application for quick note-taking that saves user input in a database.

**Database**

* The database uses SQLite.
* The SQLite table has the following columns:
	+ `id`
	+ `timestampdate`
	+ `note_type` (text, image, video, or audio)
	+ `note_content` (text or media URL)

**Note Content**

* If `note_type` is text, `note_content` stores the text.
* If `note_type` is media (image, video, or audio), `note_content` stores the URL of the uploaded media.

**Media Handling**

* Users can:
	+ Upload image, video, or audio files.
	+ Take new image, video, or audio recordings.
	+ Share media from other apps via the mobile OS sharing button.
* The app can hold files offline.

**Offline Storage and Syncing**

* When a user uploads or records media, the app attempts to upload it to the server first.
* If the upload fails due to being offline, the app stores the media locally (e.g., in offline storage) as a fallback.
* When the app comes online again, it syncs the locally stored media with the server.

**High-Level Design for Offline Storage and Syncing**

1. When a user uploads or records media, the app checks if it's online.
2. If online, the app uploads the media to the server directly.
3. If offline, the app stores the media in local offline storage (e.g., IndexedDB).
4. When the app comes online again, it checks the local offline storage for any pending uploads.
5. If there are pending uploads, the app syncs them with the server.

**Authentication**

* The app requires Google Account authentication login.

**Future Implementation**

* Docker support is planned for future implementation.
