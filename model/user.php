<?php
    /**
     * Represents a user (logged in) and all associated data
     */
    class User {
        /**
         * The ID of the user, has to be unique
         */
        private $id;
        /**
         * Whether this user has admin privileges
         */
        private $admin;
        /**
         * The theme of this user
         */
        private $theme;
        /**
         * The nickname of this user
         */
        private $nickname;
        /**
         * The next point in time when a message is allowed to prevent spam
         */
        private $chat_cooldown;
        
        public function __construct() {
            $this->id = uniqid("p", true);
            $this->admin = false;
            $this->theme = "dark";
            $this->nickname = "Meme".rand(10000, 99999);
            $this->chat_cooldown = 0;
        }
        
        /**
         * Fetches the theme loader, HTML that will initialize the user's theme
         */
        public function get_theme_loader() {
            return '<link rel="stylesheet" type="text/css" href="/css/'.$this->theme.'.css" id="theme"><script type="text/javascript">var theme = "'.$this->theme.'";</script>';
        }
        
        /**
         * Theme setter
         */
        public function set_theme($theme) {
            $this->theme = $theme;
        }
        
        /**
         * Makes this user an admin
         */
        public function escalate_privileges() {
            $this->admin = true;
        }
        
        /**
         * Nick setter
         */
        public function set_nickname($name) {
            $this->nickname = $name;
        }
        
        /**
         * Nick getter
         */
        public function get_nickname() {
            return $this->nickname;
        }
        
        /**
         * ID getter
         */
        public function get_id() {
            return $this->id;
        }
        
        /**
         * Admin status getter
         */
        public function is_admin() {
            return $this->admin;
        }
        
        /**
         * Checks whether the anti spam prevents this user from chatting
         */
        public function may_chat() {
            return time() >= $this->chat_cooldown;
        }
        
        /**
         * Prevents chatting until the given point in time has passed
         */
        public function prevent_chat_until($time) {
            $this->chat_cooldown = $time;
        }
    }
?>
