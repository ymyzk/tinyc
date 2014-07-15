tinyc
=====
Tiny C Compiler written in Python 2.

Tiny C のコードを入力して, アセンブリ言語のコードを出力する.  
出力形式は NASM (x86) と LLVM IR (x86, x64, arm...) である.
Tiny C のコードを入力し, NASM IA-32 のアセンブリのコードを出力する.  

文法
----
* Tiny C 標準 (参考文献1を参照のこと)
* コメント /\* Comment \*/
* 加算代入演算子 (+=) / 減算代入演算子 (-=)
* 前置増分演算子 (++) / 前置減分演算子 (--)

コード生成
----------
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
llvmpy を用いて, LLVM IR のコードを出力する.

最適化
------
### 構文解析
* 定数計算のコンパイル時実行 (算術/論理/比較)

### コード生成
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
* 準備中

実行方法
--------
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

テスト環境
----------
* OS X
  * NASM 2.11.05
  * clang 3.4
* Debian jessie/sid
  * NASM 2.11
  * clang 3.3
  * GCC 4.9.0

参考文献
--------
1. [計算機科学実験及演習 3（ソフトウェア）実験資料](http://www.fos.kuis.kyoto-u.ac.jp/~umatani/le3b/siryo.pdf)
2. [湯浅太一, コンパイラ (情報系教科書シリーズ), 昭晃堂, 2001](http://www.amazon.co.jp/%E3%82%B3%E3%83%B3%E3%83%91%E3%82%A4%E3%83%A9-%E6%83%85%E5%A0%B1%E7%B3%BB%E6%95%99%E7%A7%91%E6%9B%B8%E3%82%B7%E3%83%AA%E3%83%BC%E3%82%BA-%E6%B9%AF%E6%B5%85-%E5%A4%AA%E4%B8%80/dp/4785620501)
3. [IA-32 インテル® アーキテクチャー・ソフトウェア・デベロッパーズ・マニュアル、上巻: 基本アーキテクチャー](http://www.intel.co.jp/content/dam/www/public/ijkk/jp/ja/documents/developer/IA32_Arh_Dev_Man_Vol1_Online_i.pdf)
4. [IA-32 インテル® アーキテクチャー・ソフトウェア・デベロッパーズ・マニュアル、中巻 A: 命令セット・リファレンス A-M](http://www.intel.co.jp/content/dam/www/public/ijkk/jp/ja/documents/developer/IA32_Arh_Dev_Man_Vol2A_i.pdf)
5. [IA-32 インテル® アーキテクチャー・ソフトウェア・デベロッパーズ・マニュアル、中巻 B: 命令セット・リファレンス N-Z](http://www.intel.co.jp/content/dam/www/public/ijkk/jp/ja/documents/developer/IA32_Arh_Dev_Man_Vol2B_i.pdf)
6. [インテル® 64 アーキテクチャーおよび IA-32 アーキテクチャー最適化リファレンス・マニュアル](http://www.intel.co.jp/content/dam/www/public/ijkk/jp/ja/documents/developer/248966-024JA.pdf)
7. [PLY (Python Lex-Yacc)](http://www.dabeaz.com/ply/)
8. [Atul's Mini-C Compiler](http://people.cs.uchicago.edu/~varmaa/mini_c/)
