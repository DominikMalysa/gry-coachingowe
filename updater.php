<?php
/**
 * Sprawdza nowe wydania wtyczki w repozytorium GitHub i podaje je WordPressowi
 * jako zwykłą aktualizację wtyczki (Wtyczki -> Aktualizuj).
 *
 * Repozytorium prywatne: w wp-config.php dodać
 *   define( 'SSW_GC_GITHUB_TOKEN', '...' );
 * Repozytorium publiczne: token nie jest potrzebny.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

if ( ! defined( 'SSW_GC_REPO' ) ) {
	define( 'SSW_GC_REPO', 'DominikMalysa/gry-coachingowe' );
}

if ( ! function_exists( 'ssw_gc_token' ) ) {
	function ssw_gc_token() {
		return defined( 'SSW_GC_GITHUB_TOKEN' ) ? (string) SSW_GC_GITHUB_TOKEN : '';
	}
}

if ( ! function_exists( 'ssw_gc_api' ) ) {
	/** Pobiera plik z repozytorium przez API GitHuba (działa też dla repozytorium prywatnego). */
	function ssw_gc_api( $path ) {
		return 'https://api.github.com/repos/' . SSW_GC_REPO . '/contents/' . $path . '?ref=main';
	}
}

if ( ! function_exists( 'ssw_gc_latest' ) ) {
	/** Najnowsza wersja: array( 'version' => '2.3.0', 'package' => url ) albo null. */
	function ssw_gc_latest( $force = false ) {
		$cached = get_site_transient( 'ssw_gc_latest' );
		if ( ! $force && is_array( $cached ) ) {
			return $cached['version'] ? $cached : null;
		}

		$args = array(
			'timeout' => 15,
			'headers' => array(
				'Accept'     => 'application/vnd.github.raw',
				'User-Agent' => 'ssw-gry-coachingowe',
			),
		);
		$token = ssw_gc_token();
		if ( '' !== $token ) {
			$args['headers']['Authorization'] = 'Bearer ' . $token;
		}

		$res = wp_remote_get( ssw_gc_api( 'wtyczka/wersja.json' ), $args );
		if ( is_wp_error( $res ) || 200 !== (int) wp_remote_retrieve_response_code( $res ) ) {
			set_site_transient( 'ssw_gc_latest', array( 'version' => '', 'package' => '' ), 15 * MINUTE_IN_SECONDS );
			return null;
		}

		$body = json_decode( wp_remote_retrieve_body( $res ), true );
		if ( ! is_array( $body ) || empty( $body['wersja'] ) || empty( $body['plik'] ) ) {
			return null;
		}

		$out = array(
			'version' => (string) $body['wersja'],
			'package' => ssw_gc_api( 'wtyczka/' . basename( (string) $body['plik'] ) ),
		);
		set_site_transient( 'ssw_gc_latest', $out, 6 * HOUR_IN_SECONDS );
		return $out;
	}
}

add_filter(
	'pre_set_site_transient_update_plugins',
	function ( $transient ) {
		if ( ! is_object( $transient ) ) {
			return $transient;
		}
		$file = 'ssw-poznaj-siebie/ssw-poznaj-siebie.php';
		$data = get_file_data( SSW_GC_DIR . 'ssw-poznaj-siebie.php', array( 'Version' => 'Version' ) );
		$here = isset( $data['Version'] ) ? $data['Version'] : '0';

		$latest = ssw_gc_latest();
		if ( ! $latest || version_compare( $latest['version'], $here, '<=' ) ) {
			return $transient;
		}

		$transient->response[ $file ] = (object) array(
			'slug'        => 'ssw-poznaj-siebie',
			'plugin'      => $file,
			'new_version' => $latest['version'],
			'package'     => $latest['package'],
			'url'         => 'https://github.com/' . SSW_GC_REPO,
			'tested'      => get_bloginfo( 'version' ),
		);
		return $transient;
	}
);

// Pobieranie paczki z prywatnego repozytorium wymaga tokenu i nagłówka octet-stream.
add_filter(
	'http_request_args',
	function ( $args, $url ) {
		if ( 0 === strpos( (string) $url, 'https://api.github.com/repos/' . SSW_GC_REPO ) ) {
			$token                            = ssw_gc_token();
			$args['headers']                  = isset( $args['headers'] ) && is_array( $args['headers'] ) ? $args['headers'] : array();
			if ( '' !== $token ) {
				$args['headers']['Authorization'] = 'Bearer ' . $token;
			}
			$args['headers']['Accept']        = 'application/vnd.github.raw';
			$args['headers']['User-Agent']    = 'ssw-gry-coachingowe';
		}
		return $args;
	},
	10,
	2
);

// Po aktualizacji katalog z zipa ma trafić pod stałą nazwę wtyczki.
add_filter(
	'upgrader_source_selection',
	function ( $source, $remote_source, $upgrader, $hook_extra = array() ) {
		if ( empty( $hook_extra['plugin'] ) || 'ssw-poznaj-siebie/ssw-poznaj-siebie.php' !== $hook_extra['plugin'] ) {
			return $source;
		}
		$want = trailingslashit( $remote_source ) . 'ssw-poznaj-siebie';
		if ( untrailingslashit( $source ) === $want || ! is_dir( $source ) ) {
			return $source;
		}
		global $wp_filesystem;
		if ( $wp_filesystem && $wp_filesystem->move( $source, $want, true ) ) {
			return trailingslashit( $want );
		}
		return $source;
	},
	10,
	4
);

add_action(
	'upgrader_process_complete',
	function () {
		delete_site_transient( 'ssw_gc_latest' );
	}
);
