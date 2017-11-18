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
        
        public function __construct() {
            $this->id = uniqid("p", true);
            $this->admin = false;
            $this->theme = "dark";
            $this->nickname = "Meme".rand(10000, 99999);
        }
        
        /**
         * Fetches the theme loader, HTML that will initialize the user's theme
         */
        public function get_theme_loader() {
            return '<link rel="stylesheet" type="text/css" href="/css/'.$this->theme.'.css" id="theme"><script type="text/javascript">var theme = "'.$this->theme.'";</script>';
        }
        
        public function set_theme($theme) {
            $this->theme = $theme;
        }
        
        /**
         * Makes this user an admin
         */
        public function escalate_privileges() {
            $this->admin = true;
        }
        
        public function set_nickname($name) {
            $this->nickname = $name;
        }
        
        public function get_nickname() {
            return $this->nickname;
        }
        
        public function get_id() {
            return $this->id;
        }
        
        public function is_admin() {
            return $this->admin;
        }
    }
?>
