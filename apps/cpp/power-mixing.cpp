#include <NTL/ZZ_pXFactoring.h>
#include <cassert>
#include <chrono>


using namespace std;
using namespace NTL;
using namespace std::chrono;

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

Vec<ZZ_p> get_k_powers_of_b(const ZZ_p &b, const unsigned int &k)
{
    Vec<ZZ_p> bs;
    bs.SetLength(k);
    bs[0] = b;
    for (unsigned int i = 1; i < k; i++)
    {
        bs[i] = bs[i-1]*b;
    }
    return bs;
}

void benchmark(int seed, unsigned int k)
{
    // Order of MNT224
    string field_modulus_str = "150287996139850344657555064507715613525832547"
        "44125520639296541195021";
    ZZ field_modulus = conv<ZZ>(field_modulus_str.c_str());

    // Initialize the field with the modulus.
    ZZ_p::init(field_modulus);

    // Pass the same seed if you want to generate same random numbers.
    NTL::SetSeed(conv<ZZ>(seed));
    ZZ_p a = conv<ZZ_p>(RandomBnd(field_modulus)) + 1;
    ZZ_p b = conv<ZZ_p>(RandomBnd(field_modulus)) + 1;

    Vec<ZZ_p> bs = get_k_powers_of_b(b, k);
    cout << "Computed input powers!" << endl;

    high_resolution_clock::time_point t1 = high_resolution_clock::now();
    auto apows = compute_powers(a, k, bs);
    high_resolution_clock::time_point t2 = high_resolution_clock::now();

    cout << "Total Time: " << duration_cast<microseconds>( t2 - t1 ).count()
        << " microseconds!" << endl;

    cout << "a: " << a << endl;
    cout << "b: " << b << endl;
    cout << "k: " << k << endl;
    cout << "Powers of a: " << endl;
    for (int i = 1; i <= k; i++)
    {
        cout << apows[i] << endl;
    }
}

/**
 * Input:
 * field_modulus: Modulus of the field.
 * a : Number whose powers need to be computed.
 * k : Number of powers to be computed.
 * bs : k Pre computed powers of some random number.
 * */
void run_with_inputs()
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
}


int main(int argc, char* argv[])
{
    if (argc==1)
    {
        run_with_inputs();
    }
    else if (argc == 3)
    {
        unsigned int k = atoi(argv[1]);
        unsigned int seed = atoi(argv[2]);
        benchmark(seed, k);
    }

    return 0;
}