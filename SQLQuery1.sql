-- USERS
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,
    hashed_password VARCHAR(512),
    auth_provider VARCHAR(50) NOT NULL DEFAULT 'local',
    google_id VARCHAR(255) UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- GUEST_SESSIONS
CREATE TABLE IF NOT EXISTS guest_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    token VARCHAR(128) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    metadata_json JSON NULL
);

-- VIDEOS
CREATE TABLE IF NOT EXISTS videos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(512) NOT NULL,
    original_name VARCHAR(512),
    owner_id INT,
    guest_token VARCHAR(128),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata_json JSON NULL,
    CONSTRAINT FK_videos_users_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT FK_videos_guest FOREIGN KEY (guest_token) REFERENCES guest_sessions(token) ON DELETE CASCADE,
    INDEX IX_videos_owner_id (owner_id),
    INDEX IX_videos_guest_token (guest_token)
);

-- INTERVIEW_FEEDBACK_SECTIONS
CREATE TABLE IF NOT EXISTS interview_feedback_sections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    video_id INT NOT NULL,
    question_id INT NOT NULL,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    gaze_score FLOAT,
    speech_speed FLOAT,
    speech_color VARCHAR(50),
    feedback TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_sections_videos FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
    INDEX IX_sections_video_id (video_id),
    INDEX IX_sections_question_id (question_id)
);

-- FEEDBACKS
CREATE TABLE IF NOT EXISTS feedbacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    video_id INT NOT NULL,
    user_id INT,
    guest_token VARCHAR(128),
    content TEXT,
    auto_saved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_feedbacks_videos FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
    CONSTRAINT FK_feedbacks_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX IX_feedbacks_video_id (video_id),
    INDEX IX_feedbacks_user_id (user_id),
    INDEX IX_feedbacks_guest_token (guest_token)
);

-- GAZE_DATA
CREATE TABLE IF NOT EXISTS gaze_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    video_id INT NOT NULL,
    feedback_id INT,
    result_json JSON,
    raw_blob LONGBLOB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_gaze_videos FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
    CONSTRAINT FK_gaze_feedbacks FOREIGN KEY (feedback_id) REFERENCES feedbacks(id),
    INDEX IX_gaze_video_id (video_id),
    INDEX IX_gaze_feedback_id (feedback_id)
);

-- FACIAL_EXPRESSION_DATA
CREATE TABLE IF NOT EXISTS facial_expression_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    video_id INT NOT NULL,
    feedback_id INT,
    expression_json JSON,
    raw_blob LONGBLOB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_facial_videos FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
    CONSTRAINT FK_facial_feedbacks FOREIGN KEY (feedback_id) REFERENCES feedbacks(id),
    INDEX IX_facial_video_id (video_id),
    INDEX IX_facial_feedback_id (feedback_id)
);

-- INTERVIEW_RESULTS
CREATE TABLE IF NOT EXISTS interview_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    interview_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    video_file TEXT,
    audio_file TEXT,
    gaze_ratio FLOAT,
    gaze_feedback TEXT,
    gaze_color VARCHAR(50),
    expression VARCHAR(100),
    speech_speed_wpm INT,
    syllable_count INT,
    transcript LONGTEXT,
    speech_feedback TEXT,
    speech_color VARCHAR(50),
    speech_elapsed_time_sec FLOAT,
    owner_id INT,
    CONSTRAINT FK_interview_results_users FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL
);
