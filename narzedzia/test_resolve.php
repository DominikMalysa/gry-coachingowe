<?php
// Test adresów wtyczki: php test_resolve.php <ścieżka do ssw-poznaj-siebie.php> <katalog app>
define( 'ABSPATH', '/' );
function add_action() {}
function plugin_dir_path( $f ) { return dirname( $f ) . '/'; }
function get_bloginfo( $x = '' ) { return '6.0'; }
function get_site_transient( $k ) { return false; }
function set_site_transient( $k, $v, $t = 0 ) {}
function delete_site_transient( $k ) {}
function add_filter() {}
require $argv[1];
$app = $argv[2];

// [uri, home_path, method, oczekiwany typ: file|redirect|null, oczekiwana wartość (końcówka pliku lub adres)]
$cases = array(
	array( '/gry-coachingowe/', '/', 'GET', 'file', 'app/index.html' ),
	array( '/gry-coachingowe', '/', 'GET', 'redirect', '/gry-coachingowe/' ),
	array( '/gry-coachingowe/index.html', '/', 'GET', 'file', 'app/index.html' ),
	array( '/gry-coachingowe/?x=1', '/', 'GET', 'file', 'app/index.html' ),
	array( '/gry-coachingowe/stereotyp/', '/', 'GET', 'file', 'app/stereotyp/index.html' ),
	array( '/gry-coachingowe/stereotyp', '/', 'GET', 'redirect', '/gry-coachingowe/stereotyp/' ),
	array( '/gry-coachingowe/sw.js', '/', 'GET', 'file', 'app/sw.js' ),
	array( '/gry-coachingowe/manifest.webmanifest', '/', 'GET', 'file', 'app/manifest.webmanifest' ),
	array( '/gry-coachingowe/logo.png', '/', 'GET', 'file', 'app/logo.png' ),
	array( '/gry-coachingowe/fonts/lora-latin-500-normal.woff2', '/', 'GET', 'file', 'app/fonts/lora-latin-500-normal.woff2' ),
	array( '/gry-coachingowe/', '/', 'HEAD', 'file', 'app/index.html' ),
	array( '/gry-coachingowe/', '/', 'POST', 'null', '' ),
	array( '/gry-coachingowe/brak.html', '/', 'GET', 'null', '' ),
	array( '/gry-coachingowe/../wp-config.php', '/', 'GET', 'null', '' ),
	array( '/gry-coachingowe/%2e%2e/%2e%2e/wp-config.php', '/', 'GET', 'null', '' ),
	array( '/gry-coachingowe/fonts/../../ssw-poznaj-siebie.php', '/', 'GET', 'null', '' ),
	array( '/gry-coachingowe//sw.js', '/', 'GET', 'null', '' ),
	array( '/gry-coachingowe/plik.php', '/', 'GET', 'null', '' ),
	array( '/Gry-Coachingowe/', '/', 'GET', 'null', '' ),
	array( '/gry-coachingowe/STEREOTYP/', '/', 'GET', 'null', '' ),
	array( '/gry-coachingowe-inne/', '/', 'GET', 'null', '' ),
	array( '/', '/', 'GET', 'null', '' ),
	array( '/sklep/', '/', 'GET', 'null', '' ),
	// stare adresy
	array( '/stereotyp', '/', 'GET', 'redirect', '/gry-coachingowe/stereotyp/' ),
	array( '/stereotyp/', '/', 'GET', 'redirect', '/gry-coachingowe/stereotyp/' ),
	array( '/stereotyp/sw.js', '/', 'GET', 'redirect', '/gry-coachingowe/stereotyp/' ),
	array( '/stereotypy/', '/', 'GET', 'null', '' ),
	array( '/poznaj-siebie-glebiej', '/', 'GET', 'redirect', '/gry-coachingowe/' ),
	array( '/poznaj-siebie-glebiej/', '/', 'GET', 'redirect', '/gry-coachingowe/' ),
	array( '/poznaj-siebie-glebiej/stereotyp/', '/', 'GET', 'redirect', '/gry-coachingowe/stereotyp/' ),
	array( '/poznaj-siebie-glebiej/../x', '/', 'GET', 'redirect', '/gry-coachingowe/' ),
	array( '/poznaj-siebie-glebiej//evil.example/', '/', 'GET', 'redirect', '/gry-coachingowe/' ),
	array( '/poznaj-siebie-glebiej-x/', '/', 'GET', 'null', '' ),
	// WordPress w podkatalogu
	array( '/wp/gry-coachingowe/', '/wp/', 'GET', 'file', 'app/index.html' ),
	array( '/wp/gry-coachingowe', '/wp/', 'GET', 'redirect', '/wp/gry-coachingowe/' ),
	array( '/wp/stereotyp/', '/wp/', 'GET', 'redirect', '/wp/gry-coachingowe/stereotyp/' ),
	array( '/gry-coachingowe/', '/wp/', 'GET', 'null', '' ),
);

$ok = 0;
foreach ( $cases as $c ) {
	$r = ssw_ps_resolve( $c[0], $c[1], $app, $c[2] );
	if ( null === $r ) {
		$got = array( 'null', '' );
	} elseif ( isset( $r['redirect'] ) ) {
		$got = array( 'redirect', $r['redirect'] );
	} else {
		$got = array( 'file', $r['file'] );
	}
	$pass = ( $got[0] === $c[3] ) && ( 'file' === $c[3] ? ( substr( $got[1], -strlen( $c[4] ) ) === $c[4] ) : ( $got[1] === $c[4] ) );
	if ( 'file' === $c[3] && $pass && 'HEAD' === $c[2] ) {
		$pass = ( true === $r['head'] );
	}
	$ok += $pass ? 1 : 0;
	if ( ! $pass ) {
		echo "FAIL {$c[2]} {$c[0]} (home {$c[1]}): oczekiwano {$c[3]} {$c[4]}, jest {$got[0]} {$got[1]}\n";
	}
}
echo "WYNIK: $ok/" . count( $cases ) . "\n";
exit( $ok === count( $cases ) ? 0 : 1 );
