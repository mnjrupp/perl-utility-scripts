 #!/usr/bin/env perl -w
 use strict;
 use warnings;
 use MIME::Base64;
 
 # http://search.cpan.org/~mcrawfor/REST-Client/lib/REST/Client.pm
 # Example install using cpanm:
 #   sudo cpanm -i REST::Client
 use REST::Client;
 
 # Set the request parameters
 my $host = 'http://www.taskjunction.com';
 my $user = 'email:mnjrupp@hotmail.com';
 my $pwd = 'TaskJunction01';
 my $sys_id = '0818562ca8d31100a92e8545569edcb0';
 
 my $client = REST::Client->new(host => $host);
 
 my $encoded_auth = encode_base64("$user:$pwd", '');
 
 # Get the incident with sys_id declared above
 $client->GET("/api/now/table/incident/$sys_id",
              {'Authorization' => "Basic $encoded_auth",
               'Accept' => 'application/json'});
 
 print 'Response: ' . $client->responseContent() . "\n";
 print 'Response status: ' . $client->responseCode() . "\n";
 foreach ( $client->responseHeaders() ) {
   print 'Header: ' . $_ . '=' . $client->responseHeader($_) . "\n";
 }