% Reinforced concrete T-section with top and bottom reinforcements
% (potentially in multiple layers)
%
%     b
% o--------o
%
% |--------| o   o      o--> Z
% |        | |t1 |      |
% |--|  |--| o   |      |Y
%    |  |        | h
%    |  |        |
%    ----        o
%    o--o
%     t2
%
%NOTES
% * follows the row vector shaped data of Diana

function [y_i, A_i, S_i] = T_section(Concrete, Rebar)

% .........................................................................
% Concrete
% .........................................................................
% geometry
h       = Concrete.h;
b       = Concrete.b;
t1      = Concrete.t1;
t2      = Concrete.t2;

E_c     = Concrete.E;

A_c     = b.*t1 + (h-t1).*t2;
% about the top fiber
Sy_c    = b.*t1.*t1/2 + (h-t1).*t2.*(h - (h-t1)/2);
y_c     = Sy_c./A_c;

% .........................................................................
% Rebar
% .........................................................................
D_s     = Rebar.D_s;
n_s     = Rebar.n_s;
d_s     = Rebar.d_s;

E_s     = Rebar.E;

A_ss    = sum(D_s.^2*pi/4.*n_s);
d_ss    = sum(d_s.*n_s)/sum(n_s);

n_sc    = E_s/E_c;

% .........................................................................
% Idealized cross-section
% .........................................................................
A_i     = A_c + n_sc*A_ss;
% about the top fiber
S_i     = Sy_c + n_sc*A_ss*d_ss;
y_i     = S_i/A_i;

end