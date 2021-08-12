function collectiveray_theme_scripts_function() {
  wp_enqueue_script( 'js-file', get_template_directory_uri() . '/js/view.js');
}

add_action('wp_enqueue_scripts','collectiveray_theme_scripts_function');
