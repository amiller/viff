#include <NTL/ZZ_pXFactoring.h>
#include <cassert>
#include <stdio.h>

using namespace std;
using namespace NTL;

Vec<ZZ_p> compute_powers(const ZZ_p &a, const unsigned int &k, const Vec<ZZ_p> &bs)
{
    assert (bs.length() == k);

    ZZ_p b = bs[0];

    Vec<ZZ_p> apows;
    apows.SetLength(k+1);
    apows[0] = a;

    Vec<ZZ_p> DiagMinus1;
    DiagMinus1.append(ZZ_p(1));

    for (unsigned int m = 1; m <= k; m++)
    {
        Vec<ZZ_p> DiagM;
        DiagM.SetLength(m+1);
        DiagM[0]  = bs[m-1];
        ZZ_p sum(0);
        for (unsigned int i = 1; i <= m; i++)
        {
            sum += DiagMinus1[i-1];
            DiagM[i] = (a-b) * sum + bs[m-1];
        }

        apows[m] = DiagM[m];
        DiagMinus1 = DiagM;
    }

    // a^index
    apows[0] = 1;
    return apows;
}

/**
 * Input:
 * field_modulus: Modulus of the field.
 * a : Number whose powers need to be computed.
 * k : Number of powers to be computed.
 * bs : k Pre computed powers of some random number.
 * */
int main()
{
    long field_modulus;
    cin >> field_modulus;

    // Initialize the field with the modulus.
    ZZ_p::init(ZZ(field_modulus));

    ZZ_p a;
    cin >> a;

    unsigned int k;
    cin >> k;

    Vec<ZZ_p> bs;
    bs.SetLength(k);
    for (int i = 0; i < k; i++)
    {
        cin >> bs[i];
    }

    auto apows = compute_powers(a, k, bs);

    for (int i = 1; i <= k; i++)
    {
        cout << apows[i] << endl;
    }

    return 0;
}