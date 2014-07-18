# tinyc
Tiny C Compiler written in Python 2.

Tiny C のコードを入力して, アセンブリ言語のコードを出力する.  
出力形式は NASM (x86) と LLVM Assembly である.

## 文法
* Tiny C 標準 (参考文献1を参照のこと)
* コメント /\* Comment \*/
* 加算代入演算子 (+=) / 減算代入演算子 (-=)
* 前置増分演算子 (++) / 前置減分演算子 (--)

## コード生成
### NASM

利用する命令

* NASM
  * COMMON
  * EXTERN
  * GLOBAL
* x86 (IA-32)
  * 演算子
    * add
    * and
    * dec
    * idiv
    * imul
    * inc
    * neg
    * or
    * sub
    * xor
  * Call
    * call
    * ret
  * Jump / Test
    * cmp
    * je
    * jmp
    * jz
    * sete
    * setg
    * setge
    * setl
    * setle
    * setne
    * test
  * Move
    * cdq
    * mov
    * movzx
  * Stack
    * pop
    * push

### LLVM
llvmpy を用いて, LLVM Assembly のコードを作成し, 最適化パスに渡す.

## 最適化
### 構文解析
* 定数計算のコンパイル時実行 (算術/論理/比較)

### コード生成 (NASM)
* 不要な条件分岐の削除

### 最適化 (NASM)
* 重複しているラベルを削除して統合
* 利用されていないラベルの削除
* 重複する EXTERN の削除
* GLOBAL と EXTERN を先頭に括りだし
* jmp 命令後の実行されないコードの削除
* 自身の直後への jmp 命令を削除
* 不要命令の削除
 * add *R*, 0
 * sub *R*, 0
 * imul *R*, 1
* メモリストア直後のロード命令の削除
* アクセスされることのないレジスタ書き込みを削除
* 効率の良い命令への書き換え
 * imul *R* 0 -> mov *R* 0
 * mov *R* 0 -> xor *R* *R*
 * inc *R* -> add *R* 1 (参考文献6の3.5.1.1)
 * dec *R* -> sub *R* 1 (参考文献6の3.5.1.1)
* ebp 相対アクセスを esp 相対アクセスに書き換え

### 最適化 (LLVM)
`llvm-as-3.3 < /dev/null | opt-3.3 -disable-output -debug-pass=Arguments -std-compile-opts`
で出力されるパスと同じものを使用.

```
 -targetlibinfo -no-aa -tbaa -basicaa -notti -preverify -domtree
 -verify -globalopt -ipsccp -deadargelim -instcombine -simplifycfg
 -basiccg -prune-eh -inline-cost -inline -functionattrs
 -argpromotion -sroa -domtree -early-cse -simplify-libcalls
 -lazy-value-info -jump-threading -correlated-propagation
 -simplifycfg -instcombine -tailcallelim -simplifycfg -reassociate
 -domtree -loops -loop-simplify -lcssa -loop-rotate -licm -lcssa
 -loop-unswitch -instcombine -scalar-evolution -loop-simplify
 -lcssa -indvars -loop-idiom -loop-deletion -loop-unroll -memdep
 -gvn -memdep -memcpyopt -sccp -instcombine -lazy-value-info
 -jump-threading -correlated-propagation -domtree -memdep -dse
 -adce -simplifycfg -instcombine -strip-dead-prototypes -globaldce
 -constmerge -preverify -domtree -verify
```

## 実行方法
```
$ pip install git+https://github.com/litesystems/tinyc.git
$ tcc -h
```

LLVM IR のコードを出力するためには, 追加で LLVM 3.3 と,
llvmpy 0.12 が必要である.
llvmpy は setup.py の requirements にあえて指定していないので手動でインストールする.

```
$ export LLVM_CONFIG_PATH=/path/to/llvm-config
$ pip install llvmpy
```

## サンプルコード
複数のサンプルコードを準備している.

### samples_llvm
LLVM Assembly 出力のテスト用コード. `Makefile` を環境に応じて適宜修正すること.
`$ make clean dots test` とすると, 以前のコンパイル結果の削除 /
コンパイル処理 (構文木出力を含む) / Graphviz 用の dot ファイルの出力 /
テストの実行と結果の出力を行う.

### samples_nasm
NASM 出力のテスト用コード. `Makefile` を環境に応じて適宜修正すること.
`$ make clean test` とすると, 以前のコンパイル結果の削除 /
コンパイル処理 (構文木出力を含む) / テストの実行と結果の出力を行う.

### samples_report
某所での最終報告会用のテストコード. `all` と `tcln` を環境に応じて適宜修正すること.
`$ ./all` でコンパイル処理とテストの実行と結果の出力を行う.

## テスト環境
* OS X
  * NASM 2.11.05
  * clang 3.3
  * llvmpy 0.12.4
* Debian jessie/sid
  * NASM 2.11
  * clang 3.3
  * GCC 4.9.0
  * llvmpy 0.12.4

## 参考文献
1. [計算機科学実験及演習 3（ソフトウェア）実験資料](http://www.fos.kuis.kyoto-u.ac.jp/~umatani/le3b/siryo.pdf)
2. [湯浅太一, コンパイラ (情報系教科書シリーズ), 昭晃堂, 2001](http://www.amazon.co.jp/%E3%82%B3%E3%83%B3%E3%83%91%E3%82%A4%E3%83%A9-%E6%83%85%E5%A0%B1%E7%B3%BB%E6%95%99%E7%A7%91%E6%9B%B8%E3%82%B7%E3%83%AA%E3%83%BC%E3%82%BA-%E6%B9%AF%E6%B5%85-%E5%A4%AA%E4%B8%80/dp/4785620501)
3. [IA-32 インテル® アーキテクチャー・ソフトウェア・デベロッパーズ・マニュアル、上巻: 基本アーキテクチャー](http://www.intel.co.jp/content/dam/www/public/ijkk/jp/ja/documents/developer/IA32_Arh_Dev_Man_Vol1_Online_i.pdf)
4. [IA-32 インテル® アーキテクチャー・ソフトウェア・デベロッパーズ・マニュアル、中巻 A: 命令セット・リファレンス A-M](http://www.intel.co.jp/content/dam/www/public/ijkk/jp/ja/documents/developer/IA32_Arh_Dev_Man_Vol2A_i.pdf)
5. [IA-32 インテル® アーキテクチャー・ソフトウェア・デベロッパーズ・マニュアル、中巻 B: 命令セット・リファレンス N-Z](http://www.intel.co.jp/content/dam/www/public/ijkk/jp/ja/documents/developer/IA32_Arh_Dev_Man_Vol2B_i.pdf)
6. [インテル® 64 アーキテクチャーおよび IA-32 アーキテクチャー最適化リファレンス・マニュアル](http://www.intel.co.jp/content/dam/www/public/ijkk/jp/ja/documents/developer/248966-024JA.pdf)
7. [PLY (Python Lex-Yacc)](http://www.dabeaz.com/ply/)
8. [Atul's Mini-C Compiler](http://people.cs.uchicago.edu/~varmaa/mini_c/)
9. [LLVM 3.4 Documentation](http://llvm.org/docs/)
10. [llvmpy 0.12.4 documentation](http://llvmpy.org/llvmpy-doc/0.12.4/index.html)
