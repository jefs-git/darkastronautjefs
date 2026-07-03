/* =============================================================================
   Migração 001 — Adiciona campos do solicitante à tabela Sinistros
   -----------------------------------------------------------------------------
   Novos campos:
     User_ID          INT           NOT NULL  -- Identificador do usuário solicitante
     Nome_Solicitante VARCHAR(150)  NOT NULL  -- Nome do solicitante do sinistro
     Email            VARCHAR(255)  NULL      -- E-mail do solicitante
     Phone            VARCHAR(20)   NULL      -- Telefone do solicitante

   Observações:
   - A tabela Sinistros já existe em produção (Azure SQL). Por isso usamos
     ALTER TABLE ... ADD (não CREATE TABLE) e o script é idempotente:
     cada coluna só é criada se ainda não existir.
   - Colunas NOT NULL adicionadas a uma tabela que já tem linhas exigem um
     DEFAULT para não quebrar os registros existentes. Definimos DEFAULTs
     neutros (0 e '') apenas para viabilizar a migração; a aplicação sempre
     envia valores reais nos novos INSERTs.
   ============================================================================= */

SET XACT_ABORT ON;
BEGIN TRANSACTION;

-- User_ID: INT NOT NULL (com DEFAULT 0 para linhas pré-existentes)
IF COL_LENGTH('dbo.Sinistros', 'User_ID') IS NULL
BEGIN
    ALTER TABLE dbo.Sinistros
        ADD User_ID INT NOT NULL
            CONSTRAINT DF_Sinistros_User_ID DEFAULT (0);
END;

-- Nome_Solicitante: VARCHAR(150) NOT NULL (com DEFAULT '' para linhas pré-existentes)
IF COL_LENGTH('dbo.Sinistros', 'Nome_Solicitante') IS NULL
BEGIN
    ALTER TABLE dbo.Sinistros
        ADD Nome_Solicitante VARCHAR(150) NOT NULL
            CONSTRAINT DF_Sinistros_Nome_Solicitante DEFAULT ('');
END;

-- Email: VARCHAR(255) NULL
IF COL_LENGTH('dbo.Sinistros', 'Email') IS NULL
BEGIN
    ALTER TABLE dbo.Sinistros
        ADD Email VARCHAR(255) NULL;
END;

-- Phone: VARCHAR(20) NULL
IF COL_LENGTH('dbo.Sinistros', 'Phone') IS NULL
BEGIN
    ALTER TABLE dbo.Sinistros
        ADD Phone VARCHAR(20) NULL;
END;

COMMIT TRANSACTION;
