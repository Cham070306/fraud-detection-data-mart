/* One-time, non-destructive migration for an existing FraudDW database. */
USE FraudDW;
GO

IF EXISTS (
    SELECT 1
    FROM fact.FactTransaction
    GROUP BY DateKey, TimeKey, TransactionTypeKey, OrigAccountKey, DestAccountKey,
             AmountBandKey, StepRaw, Amount, OldBalanceOrig, NewBalanceOrig,
             OldBalanceDest, NewBalanceDest, IsFraud, IsFlaggedFraud
    HAVING COUNT_BIG(*) > 1
)
    THROW 51000, 'Cannot create idempotency index: duplicate business-grain facts exist.', 1;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'fact.FactTransaction')
      AND name = N'UX_FactTransaction_BusinessGrain'
)
BEGIN
    CREATE UNIQUE INDEX UX_FactTransaction_BusinessGrain
    ON fact.FactTransaction(
        DateKey, TimeKey, TransactionTypeKey, OrigAccountKey, DestAccountKey,
        AmountBandKey, StepRaw, Amount, OldBalanceOrig, NewBalanceOrig,
        OldBalanceDest, NewBalanceDest, IsFraud, IsFlaggedFraud
    );
END;
GO
