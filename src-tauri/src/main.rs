// Voorkom een extra console-venster op Windows bij release-builds.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    osv_lib::run()
}
