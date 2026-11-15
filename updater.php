<?php
/**
 * Sprawdza nowe wersje wtyczki w repozytorium GitHub i podaje je WordPressowi
 * jako zwykłą aktualizację wtyczki (Wtyczki -> Aktualizuj).
 *
 * Repozytorium publiczne: pliki pobierane są wprost z raw.githubusercontent.com.
 * Repozytorium prywatne: w wp-config.php dodać
 *   define( 'SSW_GC_GITHUB_TOKEN', '...' );
 * wtedy pliki idą przez API GitHuba z tym tokenem.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

if ( ! defined( 'SSW_GC_REPO' ) ) {
	define( 'SSW_GC_REPO', 'DominikMalysa/gry-coachingowe' );
}
if ( ! defined( 'SSW_GC_BRANCH' ) ) {
	define( 'SSW_GC_BRANCH', 'main' );
}
if ( ! defined( 'SSW_GC_PLUGIN_FILE' ) ) {
	define( 'SSW_GC_PLUGIN_FILE', 'ssw-poznaj-siebie/ssw-poznaj-siebie.php' );
}

if ( ! function_exists( 'ssw_gc_token' ) ) {
	function ssw_gc_token() {
		return defined( 'SSW_GC_GITHUB_TOKEN' ) ? trim( (string) SSW_GC_GITHUB_TOKEN ) : '';
	}
}

if ( ! function_exists( 'ssw_gc_url' ) ) {
	/** Adres pliku w repozytorium: prosty (publiczne) albo przez API (prywatne, z tokenem). */
	function ssw_gc_url( $path ) {
		if ( '' !== ssw_gc_token() ) {
			return 'https://api.github.com/repos/' . SSW_GC_REPO . '/contents/' . $path . '?ref=' . SSW_GC_BRANCH;
		}
		return 'https://raw.githubusercontent.com/' . SSW_GC_REPO . '/' . SSW_GC_BRANCH . '/' . $path;
	}
}

if ( ! function_exists( 'ssw_gc_note' ) ) {
	/** Zapisuje jednozdaniową informację o ostatnim sprawdzeniu (widoczna na liście wtyczek). */
	function ssw_gc_note( $text ) {
		set_site_transient( 'ssw_gc_note', gmdate( 'Y-m-d H:i' ) . ' UTC — ' . $text, DAY_IN_SECONDS );
	}
}

if ( ! function_exists( 'ssw_gc_latest' ) ) {
	/** Najnowsza wersja: array( 'version' => '2.3.3', 'package' => url ) albo null. */
	function ssw_gc_latest( $force = false ) {
		$cached = get_site_transient( 'ssw_gc_latest' );
		if ( ! $force && is_array( $cached ) ) {
			return $cached['version'] ? $cached : null;
		}

		$url  = ssw_gc_url( 'wtyczka/wersja.json' );
		$args = array(
			'timeout'   => 20,
			'sslverify' => true,
			'headers'   => array(
				'Accept'        => '' !== ssw_gc_token() ? 'application/vnd.github.raw' : 'application/json',
				'User-Agent'    => 'ssw-gry-coachingowe',
				'Cache-Control' => 'no-cache',
			),
		);
		if ( '' !== ssw_gc_token() ) {
			$args['headers']['Authorization'] = 'Bearer ' . ssw_gc_token();
		}

		$res = wp_remote_get( $url, $args );

		if ( is_wp_error( $res ) ) {
			ssw_gc_note( 'nie udało się połączyć: ' . $res->get_error_message() );
			set_site_transient( 'ssw_gc_latest', array( 'version' => '', 'package' => '' ), 15 * MINUTE_IN_SECONDS );
			return null;
		}
		$code = (int) wp_remote_retrieve_response_code( $res );
		if ( 200 !== $code ) {
			ssw_gc_note( 'serwer GitHuba odpowiedział kodem ' . $code );
			set_site_transient( 'ssw_gc_latest', array( 'version' => '', 'package' => '' ), 15 * MINUTE_IN_SECONDS );
			return null;
		}

		$body = json_decode( wp_remote_retrieve_body( $res ), true );
		if ( ! is_array( $body ) || empty( $body['wersja'] ) || empty( $body['plik'] ) ) {
			ssw_gc_note( 'plik z numerem wersji ma nieoczekiwaną treść' );
			set_site_transient( 'ssw_gc_latest', array( 'version' => '', 'package' => '' ), 15 * MINUTE_IN_SECONDS );
			return null;
		}

		$out = array(
			'version' => (string) $body['wersja'],
			'package' => ssw_gc_url( 'wtyczka/' . basename( (string) $body['plik'] ) ),
		);
		ssw_gc_note( 'połączenie działa; w repozytorium jest wersja ' . $out['version'] );
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

		$data = get_file_data( SSW_GC_DIR . 'ssw-poznaj-siebie.php', array( 'Version' => 'Version' ) );
		$here = isset( $data['Version'] ) ? $data['Version'] : '0';

		// „Sprawdź ponownie” w panelu ma pomijać zapamiętany wynik.
		$latest = ssw_gc_latest( ! empty( $_GET['force-check'] ) );
		if ( ! $latest ) {
			return $transient;
		}
		if ( version_compare( $latest['version'], $here, '<=' ) ) {
			return $transient;
		}

		if ( ! isset( $transient->response ) || ! is_array( $transient->response ) ) {
			$transient->response = array();
		}
		$transient->response[ SSW_GC_PLUGIN_FILE ] = (object) array(
			'id'          => SSW_GC_REPO,
			'slug'        => 'ssw-poznaj-siebie',
			'plugin'      => SSW_GC_PLUGIN_FILE,
			'new_version' => $latest['version'],
			'package'     => $latest['package'],
			'url'         => 'https://github.com/' . SSW_GC_REPO,
			'tested'      => get_bloginfo( 'version' ),
			'icons'       => array(),
			'banners'     => array(),
		);
		return $transient;
	}
);

// Pobieranie paczki z repozytorium prywatnego wymaga tokenu i surowej treści.
add_filter(
	'http_request_args',
	function ( $args, $url ) {
		$token = ssw_gc_token();
		if ( '' !== $token && 0 === strpos( (string) $url, 'https://api.github.com/repos/' . SSW_GC_REPO ) ) {
			$args['headers']                  = isset( $args['headers'] ) && is_array( $args['headers'] ) ? $args['headers'] : array();
			$args['headers']['Authorization'] = 'Bearer ' . $token;
			$args['headers']['Accept']        = 'application/vnd.github.raw';
			$args['headers']['User-Agent']    = 'ssw-gry-coachingowe';
		}
		return $args;
	},
	10,
	2
);

// Katalog z paczki ma trafić pod stałą nazwę wtyczki.
add_filter(
	'upgrader_source_selection',
	function ( $source, $remote_source, $upgrader, $hook_extra = array() ) {
		if ( empty( $hook_extra['plugin'] ) || SSW_GC_PLUGIN_FILE !== $hook_extra['plugin'] ) {
			return $source;
		}
		$want = trailingslashit( $remote_source ) . 'ssw-poznaj-siebie';
		if ( untrailingslashit( $source ) === untrailingslashit( $want ) || ! is_dir( $source ) ) {
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

// Krótka informacja o ostatnim sprawdzeniu, widoczna pod wtyczką na liście wtyczek.
add_filter(
	'plugin_row_meta',
	function ( $links, $file ) {
		if ( SSW_GC_PLUGIN_FILE !== $file || ! current_user_can( 'update_plugins' ) ) {
			return $links;
		}
		$note = get_site_transient( 'ssw_gc_note' );
		if ( ! $note ) {
			$note = 'jeszcze nie sprawdzano';
		}
		$links[] = '<span style="color:#646970">Aktualizacje: ' . esc_html( (string) $note ) . '</span>';
		return $links;
	},
	10,
	2
);
