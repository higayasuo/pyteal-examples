from algosdk.future.transaction import StateSchema
from pyteal import (
    Approve,
    Bytes,
    Cond,
    InnerTxnBuilder,
    Int,
    OnComplete,
    Seq,
    Subroutine,
    TealType,
    Txn,
    TxnField,
    TxnType,
    compileTeal,
    Mode,
    App,
    Btoi,
    Assert,
    Global,
    Expr,
    Gtxn,
)


class AppMethods:
    init = "init"
    transfer_asset = "transfer_asset"


class GlobalVariables:
    asset_id = Bytes("asset_id")
    price = Bytes("price")


global_schema = StateSchema(2, 0)
local_schema = StateSchema(0, 0)


def approval_program() -> str:
    program = Seq(
        Cond(
            [Txn.application_id() == Int(0), create()],
            [Txn.on_completion() == OnComplete.NoOp, no_op()],
            [Txn.on_completion() == OnComplete.ClearState, Approve()],
            [Txn.on_completion() == OnComplete.CloseOut, Approve()],
            [Txn.on_completion() == OnComplete.DeleteApplication, Approve()],
            [Txn.on_completion() == OnComplete.OptIn, Approve()],
            [Txn.on_completion() == OnComplete.UpdateApplication, Approve()],
        ),
        Approve(),
    )
    return compileTeal(program, Mode.Application, version=6)


def clear_state_program() -> str:
    return compileTeal(Approve(), Mode.Application, version=6)


@Subroutine(TealType.none)
def create() -> Expr:
    return Seq()


@Subroutine(TealType.none)
def no_op() -> Expr:
    return Seq(
        Cond(
            [
                Txn.application_args[0] == Bytes(AppMethods.init),
                init(),
            ],
            [
                Txn.application_args[0] == Bytes(AppMethods.transfer_asset),
                transfer_asset(),
            ],
        ),
    )


@Subroutine(TealType.none)
def init() -> Expr:
    asset_id = Txn.assets[0]
    price = Btoi(Txn.application_args[1])
    return Seq(
        check_init(),
        App.globalPut(GlobalVariables.asset_id, asset_id),
        App.globalPut(GlobalVariables.price, price),
    )


@Subroutine(TealType.none)
def check_init() -> Expr:
    return Seq(
        Assert(Global.group_size() == Int(2)),
        check_init_call_app(Int(0)),
        check_init_payment(Int(1)),
    )


@Subroutine(TealType.none)
def check_init_call_app(gtxn_index: Expr) -> Expr:
    return Seq(
        check_zero_addresses(gtxn_index),
    )


@Subroutine(TealType.none)
def check_init_payment(gtxn_index: Expr) -> Expr:
    return Seq(
        check_zero_addresses(gtxn_index),
    )


@Subroutine(TealType.none)
def check_zero_addresses(gtxn_index: Expr) -> Expr:
    return Seq(
        Assert(Gtxn[gtxn_index].rekey_to() == Global.zero_address()),
        Assert(Gtxn[gtxn_index].close_remainder_to() == Global.zero_address()),
        Assert(Gtxn[gtxn_index].asset_close_to() == Global.zero_address()),
    )


@Subroutine(TealType.none)
def transfer_asset() -> Expr:
    return Seq(
        transfer_asset_txn(),
    )


@Subroutine(TealType.none)
def transfer_asset_txn() -> Expr:
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.asset_sender: Txn.accounts[1],
                TxnField.asset_receiver: Txn.sender(),
                TxnField.xfer_asset: Txn.assets[0],
                TxnField.asset_amount: Int(1),
            }
        ),
        InnerTxnBuilder.Submit(),
    )


def main() -> None:
    print(approval_program())


if __name__ == "__main__":
    main()
