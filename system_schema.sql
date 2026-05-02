-- SQL schema extracted from db.sqlite3 (Django + forum)


-- auth_group
CREATE TABLE "auth_group" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(150) NOT NULL UNIQUE);

-- auth_group_permissions
CREATE TABLE "auth_group_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);

-- auth_permission
CREATE TABLE "auth_permission" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "content_type_id" integer NOT NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "codename" varchar(100) NOT NULL, "name" varchar(255) NOT NULL);

-- auth_user
CREATE TABLE "auth_user" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "password" varchar(128) NOT NULL, "last_login" datetime NULL, "is_superuser" bool NOT NULL, "username" varchar(150) NOT NULL UNIQUE, "last_name" varchar(150) NOT NULL, "email" varchar(254) NOT NULL, "is_staff" bool NOT NULL, "is_active" bool NOT NULL, "date_joined" datetime NOT NULL, "first_name" varchar(150) NOT NULL);

-- auth_user_groups
CREATE TABLE "auth_user_groups" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED);

-- auth_user_user_permissions
CREATE TABLE "auth_user_user_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);

-- django_admin_log
CREATE TABLE "django_admin_log" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "object_id" text NULL, "object_repr" varchar(200) NOT NULL, "action_flag" smallint unsigned NOT NULL CHECK ("action_flag" >= 0), "change_message" text NOT NULL, "content_type_id" integer NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "action_time" datetime NOT NULL);

-- django_content_type
CREATE TABLE "django_content_type" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app_label" varchar(100) NOT NULL, "model" varchar(100) NOT NULL);

-- django_migrations
CREATE TABLE "django_migrations" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app" varchar(255) NOT NULL, "name" varchar(255) NOT NULL, "applied" datetime NOT NULL);

-- django_session
CREATE TABLE "django_session" ("session_key" varchar(40) NOT NULL PRIMARY KEY, "session_data" text NOT NULL, "expire_date" datetime NOT NULL);

-- forum_adminactivitylog
CREATE TABLE "forum_adminactivitylog" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "action_type" varchar(30) NOT NULL, "action_description" text NOT NULL, "status" varchar(20) NOT NULL, "error_message" text NOT NULL, "ip_address" char(39) NULL, "created_at" datetime NOT NULL, "admin_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "target_comment_id" bigint NULL REFERENCES "forum_comment" ("id") DEFERRABLE INITIALLY DEFERRED, "target_post_id" bigint NULL REFERENCES "forum_post" ("id") DEFERRABLE INITIALLY DEFERRED, "target_user_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);

-- forum_category
CREATE TABLE "forum_category" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(100) NOT NULL, "slug" varchar(120) NOT NULL UNIQUE, "color_dot" varchar(20) NOT NULL, "description" text NULL, "created_at" datetime NOT NULL);

-- forum_comment
CREATE TABLE "forum_comment" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "content" text NOT NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "author_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "post_id" bigint NOT NULL REFERENCES "forum_post" ("id") DEFERRABLE INITIALLY DEFERRED, "is_hidden" bool NOT NULL, "report_count" integer NOT NULL, "verified_at" datetime NULL, "verified_by_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "verified_by_expert" bool NOT NULL);

-- forum_comment_likes
CREATE TABLE "forum_comment_likes" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "comment_id" bigint NOT NULL REFERENCES "forum_comment" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);

-- forum_notification
CREATE TABLE "forum_notification" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "notification_type" varchar(20) NOT NULL, "title" varchar(255) NOT NULL, "message" text NOT NULL, "is_read" bool NOT NULL, "read_at" datetime NULL, "created_at" datetime NOT NULL, "comment_id" bigint NULL REFERENCES "forum_comment" ("id") DEFERRABLE INITIALLY DEFERRED, "post_id" bigint NULL REFERENCES "forum_post" ("id") DEFERRABLE INITIALLY DEFERRED, "recipient_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);

-- forum_otptoken
CREATE TABLE "forum_otptoken" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "email" varchar(254) NOT NULL, "otp_code" varchar(6) NOT NULL, "otp_type" varchar(20) NOT NULL, "created_at" datetime NOT NULL, "expires_at" datetime NOT NULL, "is_used" bool NOT NULL);

-- forum_post
CREATE TABLE "forum_post" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "title" varchar(255) NOT NULL, "content" text NOT NULL, "verified_by_expert" bool NOT NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "author_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "category_id" bigint NOT NULL REFERENCES "forum_category" ("id") DEFERRABLE INITIALLY DEFERRED, "image" varchar(100) NULL, "is_hidden" bool NOT NULL, "privacy" varchar(20) NOT NULL, "report_count" integer NOT NULL, "verification_reason" varchar(20) NOT NULL, "verified_at" datetime NULL, "verified_by_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);

-- forum_post_likes
CREATE TABLE "forum_post_likes" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "post_id" bigint NOT NULL REFERENCES "forum_post" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);

-- forum_postimage
CREATE TABLE "forum_postimage" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "image" varchar(100) NOT NULL, "alt_text" varchar(255) NOT NULL, "order" integer unsigned NOT NULL CHECK ("order" >= 0), "created_at" datetime NOT NULL, "post_id" bigint NOT NULL REFERENCES "forum_post" ("id") DEFERRABLE INITIALLY DEFERRED);

-- forum_report
CREATE TABLE "forum_report" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "report_type" varchar(20) NOT NULL, "reason" text NOT NULL, "is_processed" bool NOT NULL, "processed_at" datetime NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "comment_id" bigint NULL REFERENCES "forum_comment" ("id") DEFERRABLE INITIALLY DEFERRED, "post_id" bigint NULL REFERENCES "forum_post" ("id") DEFERRABLE INITIALLY DEFERRED, "processed_by_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "reporter_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);

-- forum_systemsettings
CREATE TABLE "forum_systemsettings" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "key" varchar(50) NOT NULL UNIQUE, "value" text NOT NULL, "description" text NOT NULL, "updated_at" datetime NOT NULL, "updated_by_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);

-- forum_userprofile
CREATE TABLE "forum_userprofile" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_type" varchar(20) NOT NULL, "is_verified_doctor" bool NOT NULL, "bio" text NOT NULL, "avatar" varchar(100) NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "user_id" integer NOT NULL UNIQUE REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);

-- forum_userprofile_interested_categories
CREATE TABLE "forum_userprofile_interested_categories" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "userprofile_id" bigint NOT NULL REFERENCES "forum_userprofile" ("id") DEFERRABLE INITIALLY DEFERRED, "category_id" bigint NOT NULL REFERENCES "forum_category" ("id") DEFERRABLE INITIALLY DEFERRED);
