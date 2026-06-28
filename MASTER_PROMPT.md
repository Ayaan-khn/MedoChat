# MEDOCHAT MASTER PROJECT SPECIFICATION

You are the lead software engineer responsible for building MedoChat.

Your goal is NOT to create a demo or tutorial project.

Your goal is to build a professional, production-quality messaging platform suitable for a software engineering portfolio.

## General Rules

* Never generate placeholder or incomplete code when a complete implementation is reasonable.
* Never break existing functionality while adding new features.
* Maintain a clean architecture.
* Keep all code modular.
* Every file should have a single responsibility.
* Do not duplicate code.
* Preserve the existing MedoChat branding and dark futuristic UI.
* Use responsive design from the beginning.
* Use semantic HTML.
* Use modern CSS.
* Use vanilla JavaScript unless another library is specifically justified.
* Backend must use Python with Flask.
* Real-time messaging must use Flask-SocketIO.
* Use SQLAlchemy as the ORM.
* Use SQLite for local development and PostgreSQL compatibility for deployment.
* Store all configuration in environment variables.
* Never hardcode credentials.
* Generate a `.env.example` and ensure `.env` is excluded from version control.

## Project Structure

Respect the existing project structure while improving organization where necessary.

Use dedicated folders for:

* Backend
* Frontend
* Routes
* Models
* Services
* Utilities
* Database
* Uploads
* Logs
* Configuration
* Static assets

Each HTML page must have its own CSS file and JavaScript file.

## UI & Branding

Maintain a consistent visual identity:

* Phoenix logo on every page.
* Dark blue theme with orange logo accents.
* Glassmorphism.
* Smooth animations.
* Consistent typography.
* Responsive layouts for desktop and mobile.

## Core Pages

* Landing Page
* Login
* Signup
* About
* User Profile
* Settings
* Chat Interface
* Friends
* Notifications
* Admin Dashboard (hidden, separate route)

## Authentication

Implement:

* Signup
* Login
* Logout
* Email verification
* Forgot password
* Reset password
* Password change
* Remember me
* Session management
* Bcrypt password hashing

## Profiles

Each user has:

* Unique User ID
* Username
* Display Name
* QR Code
* Email
* Bio
* Profile Picture
* Cover Photo
* Stories
* Status
* Join Date
* Last Seen
* Online Status

## Friends

Implement:

* Friend Requests
* Accept
* Reject
* Cancel
* Remove Friend
* Block User
* Search by Username
* Search by User ID
* Add via QR Code

## Messaging

Support:

* Real-time one-to-one chat
* Group chat
* Typing indicator
* Delivered
* Seen
* Message timestamps
* Reply
* Forward
* Copy
* Edit
* Delete for Me
* Delete for Everyone
* Pinned chats
* Search messages
* Emoji picker
* Favorite emojis
* Voice notes
* Image sharing
* Document sharing (100 MB max)

## Groups

Support:

* Group Icon
* Description
* Invite Links
* Join Requests
* Admins
* Moderators
* Member Roles

## Stories

Implement 24-hour stories supporting text, images, and videos.

## AI

Create a dedicated Medo AI conversation supporting:

* General Q&A
* Chat summarization
* Rewrite text
* "Polish My English"
* Code explanation
* Code generation
* Web search integration
* File analysis

Design the AI integration so the provider can be changed through configuration.

## Notifications

Support:

* Browser notifications
* Desktop notifications
* PWA notifications
* Badge counters
* Notification sounds

## Settings

Allow users to configure:

* Theme
* Accent color
* Font
* Privacy
* Password
* Notifications

## Security

Implement:

* CSRF protection
* SQL injection protection
* XSS protection
* Rate limiting
* Brute-force protection
* Secure cookies
* Input validation

## Logging

Log important events and errors with timestamps.

## File Storage

Store uploads in organized folders during development. Design storage so it can later migrate to cloud object storage without major refactoring.

## Deployment

Design for:

* Local development with SQLite
* Deployment with PostgreSQL
* Installable Progressive Web App
* Responsive desktop and mobile experience

## Admin

Create a hidden administrator dashboard that is not linked from the public interface.

Support:

* User management
* Group management
* Server statistics
* Logs
* Announcements
* Database backups
* Storage management

## Code Quality

Prefer readability over cleverness.

Document complex logic with concise comments.

Avoid excessively large files.

Use reusable components and helper functions where appropriate.

## Development Workflow

Do not generate the entire project in a single step.

Implement features module by module while preserving architectural consistency.

At the end of each completed module:

* Verify it integrates with previous modules.
* Fix issues before proceeding.
* Avoid introducing regressions.

The final result should feel like a cohesive communication platform rather than a collection of disconnected features.
