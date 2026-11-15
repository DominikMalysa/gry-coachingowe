<?php
// Mini-atrapa WordPressa do testu wtyczki: php -S 127.0.0.1:8765 router.php (zmienna PLUGIN = ścieżka do pliku wtyczki)
define( 'ABSPATH', '/' );
$GLOBALS['hooks'] = array();
function add_action( $name, $fn ) { $GLOBALS['hooks'][] = $fn; }
function home_url( $p = '/' ) { return 'http://127.0.0.1:8765' . $p; }
function plugin_dir_path( $f ) { return dirname( $f ) . '/'; }
function get_bloginfo( $x = '' ) { return '6.0'; }
function get_site_transient( $k ) { return false; }
function set_site_transient( $k, $v, $t = 0 ) {}
function delete_site_transient( $k ) {}
function add_filter() {}
if ( ! defined( 'MINUTE_IN_SECONDS' ) ) { define( 'MINUTE_IN_SECONDS', 60 ); }
if ( ! defined( 'HOUR_IN_SECONDS' ) ) { define( 'HOUR_IN_SECONDS', 3600 ); }
function status_header( $c ) { http_response_code( $c ); }
require getenv( 'PLUGIN' );
foreach ( $GLOBALS['hooks'] as $fn ) { $fn(); }
http_response_code( 404 );
echo 'WP: nie ma takiej strony';
