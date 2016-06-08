#!perl -w
use strict;
use FindBin;
use lib "$FindBin::Bin/lib";

use Pegex;
#use TAP::Runner;

my $grammar = <<'...';
# Precedence Climbing grammar:
expr: add-sub
add-sub: mul-div+ % /- ( [ '+-' ])/
mul-div: power+ % /- ([ '*/' ])/
power: token+ % /- '^' /
token: /- '(' -/ expr /- ')'/ | number
number: /- ( '-'? DIGIT+ )/
...

{
    package Calculator;
    use base 'Pegex::Tree';

    sub gotrule {
        my ($self, $list) = @_;
        return $list unless ref $list;

        # Right associative:
        if ($self->rule eq 'power') {
            while (@$list > 1) {
                my ($a, $b) = splice(@$list, -2, 2);
                push @$list, $a ** $b;
            }
        }
        # Left associative:
        else {
            while (@$list > 1) {
                my ($a, $op, $b) = splice(@$list, 0, 3);
                unshift @$list,
                    ($op eq '+') ? ($a + $b) :
                    ($op eq '-') ? ($a - $b) :
                    ($op eq '*') ? ($a * $b) :
                    ($op eq '/') ? ($a / $b) :
                    die;
            }
        }
        return @$list;
    }
}

# TAP::Runner->new(args => \@ARGV)->run(
    # sub { pegex($grammar, 'Calculator')->parse($_[0]) }
# );

 while (1) {
        print "\nEnter an equation: ";
        my $input = <>;
        chomp $input;
        last unless length $input;
        calc($input);
    }

    sub calc {
        my $expr = shift;
        my $calculator = pegex($grammar, 'Calculator');
        my $result = eval { $calculator->parse($expr) };
        print $@ || "$expr = $result\n";
    }