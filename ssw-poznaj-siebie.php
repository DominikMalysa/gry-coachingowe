<?php
/**
 * Plugin Name: Świadome Słowa — Gry coachingowe
 * Description: Udostępnia zakładkę „Gry coachingowe” (strona główna i gry) pod adresem /gry-coachingowe/ jako aplikację do zainstalowania na telefonie i komputerze. Stare adresy /stereotyp/ i /poznaj-siebie-glebiej/ przekierowują do nowej lokalizacji. Wyłączenie wtyczki wyłącza te strony. Nie zmienia żadnych innych stron ani ustawień. Zastępuje wtyczkę „Stereotyp na warsztacie” (wyłącz ją przed włączeniem tej).
 * Version: 2.3.3
 * Author: Dominik Małysa
 * Text Domain: ssw-poznaj-siebie
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

if ( ! defined( 'SSW_GC_DIR' ) ) {
	define( 'SSW_GC_DIR', plugin_dir_path( __FILE__ ) );
}

// Sprawdzanie i instalowanie nowych wersji prosto z repozytorium GitHub.
require_once __DIR__ . '/updater.php';

if ( ! defined( 'SSW_PS_NOINDEX' ) ) {
	// true = wyszukiwarki nie indeksują stron (tryb testowy). Po publicznym starcie ustaw false.
	define( 'SSW_PS_NOINDEX', true );
}

if ( ! function_exists( 'ssw_ps_resolve' ) ) {
	/**
	 * Zwraca opis odpowiedzi dla adresów /gry-coachingowe/... oraz starych /stereotyp/... i /poznaj-siebie-glebiej/... albo null.
	 * Pliki są serwowane wyłącznie z katalogu app wtyczki, tylko dozwolone rozszerzenia i znaki,
	 * bez ścieżek wychodzących poza katalog.
	 */
	function ssw_ps_resolve( $request_uri, $home_path, $app_dir, $method = 'GET' ) {
		$types = array(
			'html'        => 'text/html; charset=utf-8',
			'js'          => 'text/javascript; charset=utf-8',
			'css'         => 'text/css; charset=utf-8',
			'json'        => 'application/json; charset=utf-8',
			'webmanifest' => 'application/manifest+json; charset=utf-8',
			'png'         => 'image/png',
			'jpg'         => 'image/jpeg',
			'svg'         => 'image/svg+xml',
			'woff2'       => 'font/woff2',
		);
		$long = array( 'png', 'jpg', 'svg', 'woff2' );

		if ( ! in_array( $method, array( 'GET', 'HEAD' ), true ) ) {
			return null;
		}

		$path = rawurldecode( (string) parse_url( (string) $request_uri, PHP_URL_PATH ) );
		$base = rtrim( (string) $home_path, '/' );
		if ( '' !== $base ) {
			if ( $path !== $base && 0 !== strpos( $path, $base . '/' ) ) {
				return null;
			}
			$path = substr( $path, strlen( $base ) );
		}
		$path = '/' . ltrim( $path, '/' );

		// Stary adres gry: /stereotyp i /stereotyp/ -> nowa lokalizacja (trwałe przekierowanie).
		if ( '/stereotyp' === $path || '/stereotyp/' === $path ) {
			return array( 'redirect' => $base . '/gry-coachingowe/stereotyp/' );
		}
		// Stare podadresy gry (sw.js, manifest) nie są już serwowane; stary service worker ma się zaktualizować.
		if ( 0 === strpos( $path, '/stereotyp/' ) ) {
			return array( 'redirect' => $base . '/gry-coachingowe/stereotyp/' );
		}

		$root = '/gry-coachingowe';

		// Wcześniejszy adres roboczy /poznaj-siebie-glebiej/... -> ten sam podadres pod /gry-coachingowe/ (trwałe przekierowanie).
		$old = '/poznaj-siebie-glebiej';
		if ( $path === $old || 0 === strpos( $path, $old . '/' ) ) {
			$tail = (string) substr( $path, strlen( $old ) );
			if ( '' === $tail ) {
				$tail = '/';
			}
			if ( ! preg_match( '#^/[a-z0-9._/-]*$#', $tail ) || false !== strpos( $tail, '..' ) || false !== strpos( $tail, '//' ) ) {
				$tail = '/';
			}
			return array( 'redirect' => $base . $root . $tail );
		}
		if ( $path === $root ) {
			return array( 'redirect' => $base . $root . '/' );
		}
		if ( 0 !== strpos( $path, $root . '/' ) ) {
			return null;
		}

		$rel = substr( $path, strlen( $root . '/' ) );
		if ( '' === $rel || '/' === substr( $rel, -1 ) ) {
			$rel .= 'index.html';
		}
		// Katalog bez ukośnika na końcu (np. /stereotyp) -> z ukośnikiem, żeby ścieżki względne działały.
		if ( false === strpos( basename( $rel ), '.' ) ) {
			return array( 'redirect' => $base . $root . '/' . $rel . '/' );
		}

		if ( ! preg_match( '#^[a-z0-9][a-z0-9._/-]*$#', $rel ) || false !== strpos( $rel, '..' ) || false !== strpos( $rel, '//' ) ) {
			return null;
		}
		$ext = strtolower( (string) pathinfo( $rel, PATHINFO_EXTENSION ) );
		if ( ! isset( $types[ $ext ] ) ) {
			return null;
		}

		$dir  = realpath( $app_dir );
		$file = $dir ? realpath( $dir . '/' . $rel ) : false;
		if ( false === $file || 0 !== strpos( $file, $dir . DIRECTORY_SEPARATOR ) || ! is_file( $file ) ) {
			return null;
		}

		return array(
			'file' => $file,
			'type' => $types[ $ext ],
			'long' => in_array( $ext, $long, true ),
			'head' => ( 'HEAD' === $method ),
		);
	}
}

add_action(
	'plugins_loaded',
	function () {
		if ( empty( $_SERVER['REQUEST_URI'] ) ) {
			return;
		}
		$method    = isset( $_SERVER['REQUEST_METHOD'] ) ? strtoupper( (string) $_SERVER['REQUEST_METHOD'] ) : 'GET';
		$home_path = (string) parse_url( home_url( '/' ), PHP_URL_PATH );
		$r         = ssw_ps_resolve( $_SERVER['REQUEST_URI'], $home_path, plugin_dir_path( __FILE__ ) . 'app', $method );

		if ( null === $r ) {
			return;
		}

		if ( ! defined( 'DONOTCACHEPAGE' ) ) {
			define( 'DONOTCACHEPAGE', true );
		}

		if ( isset( $r['redirect'] ) ) {
			header( 'Location: ' . $r['redirect'], true, 301 );
			exit;
		}

		status_header( 200 );
		header( 'Content-Type: ' . $r['type'] );
		if ( SSW_PS_NOINDEX ) {
			header( 'X-Robots-Tag: noindex, nofollow' );
		}
		header( 'Cache-Control: ' . ( $r['long'] ? 'public, max-age=604800' : 'no-cache, must-revalidate' ) );
		if ( ! $r['head'] ) {
			readfile( $r['file'] );
		}
		exit;
	},
	1
);
