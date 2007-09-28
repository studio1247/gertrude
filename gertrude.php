<?php

$token_filename = "./.token";
$db_filename = "./gertrude.db";

$token = $HTTP_GET_VARS["token"];

function check_token() {
  global $token_filename;
  global $token;

  if (!file_exists($token_filename))
    return 0;

  $fp = fopen($token_filename, 'r');
  $ftoken = trim(fgets($fp, 4096));
  fclose($fp);

  if ($token != $ftoken)
    return 0;

  return 1;
}

function get_token() {
  global $token_filename;

  if (file_exists($token_filename))
    return 0;

  $token = uniqid(md5(rand()), true);
  $f = fopen($token_filename, "w");
  fputs($f, $token);
  fclose($f);
  return $token;
}

function rel_token() {
  global $token_filename;

  if (!check_token())
    return 0;

  unlink($token_filename);
  return 1;
}

function upload() {
  global $db_filename;

  if (!check_token())
    return 0;

  $tmp_file = $_FILES['database']['tmp_name'];
  if (!is_uploaded_file($tmp_file))
    return 0;

  if (file_exists($db_filename)) {
    $backup_filename = "backup_" . time() . ".db";
    if (!copy($db_filename, $backup_filename))
      return 0;
  }

  if (!move_uploaded_file($tmp_file, $db_filename))
    return 0;

  return 1;
}

function download() {
  global $db_filename;

  if (!file_exists($db_filename))
    return 0;
    
  $fp = fopen($db_filename, 'r');
  $data = fread($fp, filesize($db_filename));
  return $data;
}

function get_version($prefix, $suffix) {
   $dh = opendir(".");
   while (false !== ($file = readdir($dh))) {
     if (substr($file, 0, strlen($prefix)) == $prefix && substr($file, 0-strlen($suffix), strlen($suffix)) == $suffix) {
       $version = substr($file, strlen($prefix), strlen($file)-strlen($prefix)-strlen($suffix));
       return $version;
     }
   }
}

function execute($action) {
  switch($action) {
    case "has_token":
      return check_token();
    case "get_token":
      return get_token();
    case "rel_token":
      return rel_token();
    case "upload":
      return upload();
    case "download":
      return download();
    case "get_exe_version":
      return get_version("gertrude_", ".exe");
    case "get_templates_version":
      return get_version("templates_", ".zip");
  }
}

echo execute($HTTP_GET_VARS["action"]);

?>
