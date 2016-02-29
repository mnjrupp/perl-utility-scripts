use warnings;
use strict;
use HTTP::Daemon;
use HTTP::Status;
use Data::Dumper;

  my $d = HTTP::Daemon->new(
           LocalAddr => '127.0.0.1',
           LocalPort => 3000,
       ) || die;
  print "Please contact me at: <URL:", $d->url, ">\n";
  while (my $c = $d->accept) {
      while (my $r = $c->get_request) {
	      #print $d->url,"\n";
		  #print Dumper($r);
          if ($r->method eq 'GET'){
		    print $r->uri->path =~/\/.+\.htm/,"\n";
		    if($r->uri->path =~/\/d3\/.+\.json/) {
			 my $cleanpath=$r->uri->path;
			 $cleanpath=~s/^.+\///;
              # remember, this is *not* recommended practice :-)
              $c->send_file_response($cleanpath);
			  print "Sending file $cleanpath\n";
			}
			if($r->uri->path =~/\/d3\/.+\.csv/) {
			 my $cleanpath=$r->uri->path;
			 $cleanpath=~s/^.+\///;
              # remember, this is *not* recommended practice :-)
              $c->send_file_response($cleanpath);
			  print "Sending file $cleanpath\n";
			}
			if($r->uri->path =~ /\/.+\.htm/){
			  my $cleanpath=$r->uri->path;
				$cleanpath=~s/\///;
				print $cleanpath,"\n";
				$c->send_file_response($cleanpath);
				print "Sending file $cleanpath\n";
			}
			if($r->uri->path =~ /\/.+\.html/){
			  my $cleanpath=$r->uri->path;
				$cleanpath=~s/\///;
				print $cleanpath,"\n";
				$c->send_file_response($cleanpath);
				print "Sending file $cleanpath\n";
			}
			if($r->uri->path =~ /\/.+\.png/){
			  my $cleanpath=$r->uri->path;
				$cleanpath=~s/\///;
				print $cleanpath,"\n";
				$c->send_file_response($cleanpath);
				print "Sending file $cleanpath\n";
			}
			if($r->uri->path eq '/d3.min.js'){
				$c->send_file_response('d3.min.js');
				print "Sending file d3.min.js\n";
			}
		  }
		   
          else {
              $c->send_error(RC_FORBIDDEN)
          }
      }
      $c->close;
      undef($c);
	  print "Closing Connection\n";
  }